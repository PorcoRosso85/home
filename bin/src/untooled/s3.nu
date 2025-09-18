#!/usr/bin/env -S nix shell nixpkgs#s3cmd nixpkgs#oci-cli -c nu

# s3cmdコマンドとociコマンドを試験的に呼び出すmain関数
def check_commands [] {
    print "コマンド確認を実行します"
    let s3cmd_version = (s3cmd --version | complete)
    let oci_version = (oci --version | complete)
    
    if $s3cmd_version.exit_code == 0 and $oci_version.exit_code == 0 {
        print "s3cmdコマンドとociコマンドが使用可能です"
        print $"s3cmd: ($s3cmd_version.stdout)"
        print $"oci: ($oci_version.stdout)"
        return true
    } else {
        print "コマンドの確認に失敗しました"
        if $s3cmd_version.exit_code != 0 { print $"s3cmd エラー: ($s3cmd_version.stderr)" }
        if $oci_version.exit_code != 0 { print $"oci エラー: ($oci_version.stderr)" }
        return false
    }
}

# OCIオブジェクトストレージバケットインスタンスを作成する
def create_oci_bucket [
    --name(-n): string = "test-bucket",
    --compartment-id(-c): string, # ユーザーが明示的に指定する場合
    --namespace(-s): string       # ユーザーが明示的に指定する場合
] {
    print $"OCI バケット「($name)」を作成します"
    
    # OCI設定の確認
    let oci_config_exists = ("~/.oci/config" | path expand | path exists)
    if not $oci_config_exists {
        print "警告: OCI設定ファイル(~/.oci/config)が見つかりません"
        if $compartment_id == null or $namespace == null {
            print "エラー: OCI設定がないため、--compartment-id と --namespace を明示的に指定する必要があります"
            print "例: s3.nu --create-bucket mybucket --compartment-id ocid1.compartment.oc1.. --namespace mynamespace"
            return false
        }
    }
    
    # コンパートメントIDを取得または使用
    let compartment_id_value = if $compartment_id != null {
        # ユーザーが明示的に指定した場合はそれを使用
        print $"指定されたコンパートメントIDを使用: ($compartment_id)"
        $compartment_id
    } else {
        # 自動取得を試みる
        print "コンパートメントIDを取得中..."
        
        # ルートコンパートメントID取得を試みる
        let tenant_result = (oci iam tenancy get --config-file ~/.oci/config | complete)
        
        if $tenant_result.exit_code != 0 {
            print "ルートコンパートメントID(テナントID)の取得に失敗しました"
            print "エラー: コンパートメントIDを --compartment-id オプションで明示的に指定してください"
            print $tenant_result.stderr
            return false
        }
        
        let tenant_data = ($tenant_result.stdout | from json)
        let tenant_id = $tenant_data.data.id
        
        print $"ルートコンパートメントID (テナントID): ($tenant_id)"
        $tenant_id
    }
    
    # Namespaceを取得または使用
    let namespace_value = if $namespace != null {
        # ユーザーが明示的に指定した場合はそれを使用
        print $"指定されたNamespaceを使用: ($namespace)"
        $namespace
    } else {
        # 自動取得を試みる
        print "Namespaceを取得中..."
        let namespace_result = (oci os ns get | complete)
        
        if $namespace_result.exit_code != 0 {
            print "Namespaceの取得に失敗しました"
            print "エラー: Namespaceを --namespace オプションで明示的に指定してください"
            print $namespace_result.stderr
            return false
        }
        
        let namespace_data = ($namespace_result.stdout | from json)
        let ns = $namespace_data.data
        
        print $"取得したNamespace: ($ns)"
        $ns
    }
    
    # バケットを作成
    print "バケットを作成中..."
    let create_result = (oci os bucket create --compartment-id $compartment_id_value --namespace $namespace_value --name $name | complete)
    
    if $create_result.exit_code == 0 {
        print $"バケット「($name)」の作成に成功しました"
        print $create_result.stdout
        return true
    } else {
        print $"バケット「($name)」の作成に失敗しました"
        print $create_result.stderr
        return false
    }
}

# S3環境変数のチェック
def check_env_vars [] {
    print "環境変数を確認します"
    
    if ($env | get -i S3_ACCESS_KEY_ID) != null and ($env | get -i S3_SECRET_ACCESS_KEY) != null {
        print "S3環境変数が設定されています"
        return true
    } else {
        print "FIX: 以下の環境変数を設定してください:"
        print "- S3_ACCESS_KEY_ID"
        print "- S3_SECRET_ACCESS_KEY"
        return false
    }
}

# s3cfg設定ファイルの作成
def create_s3cfg [] {
    print "~/.s3cfgファイルを作成します"
    
    if not (check_env_vars) {
        return false
    }
    
    let config = $"""
    [default]
    access_key = ($env.S3_ACCESS_KEY_ID)
    secret_key = ($env.S3_SECRET_ACCESS_KEY)
    host_base = storage.googleapis.com
    host_bucket = %(bucket)s.storage.googleapis.com
    use_https = True
    """
    
    try {
        $config | save ~/.s3cfg
        print "~/.s3cfgファイルを作成しました"
        return true
    } catch {
        print "エラー: ~/.s3cfgファイルの作成に失敗しました"
        return false
    }
}

# S3接続テスト
def test_connection [] {
    print "S3接続をテストします"
    
    # s3cmdのpingコマンドは存在しないため、lsコマンドで接続テスト
    let test_result = (s3cmd ls | complete)
    
    if $test_result.exit_code == 0 {
        print "S3接続テスト成功"
        print $test_result.stdout
        return true
    } else {
        print "S3接続テスト失敗"
        print $test_result.stderr
        return false
    }
}

# テストファイルのアップロード
def upload_test_file [--bucket(-b): string, --file(-f): string = "test-file.txt"] {
    if $bucket == null {
        print "エラー: バケット名を指定してください (--bucket オプション)"
        return false
    }
    
    print $"テストファイル「($file)」を作成してバケット「($bucket)」にアップロードします"
    
    # テストファイルを作成
    "This is a test file for S3 upload test." | save $file
    
    # ファイルをアップロード
    let upload_result = (s3cmd put $file s3://$bucket/ | complete)
    
    if $upload_result.exit_code == 0 {
        print "ファイルのアップロードに成功しました"
        print $upload_result.stdout
        return true
    } else {
        print "ファイルのアップロードに失敗しました"
        print $upload_result.stderr
        return false
    }
}

# ファイルのダウンロード
def download_test_file [--bucket(-b): string, --file(-f): string = "test-file.txt", --output(-o): string = "downloaded-file.txt"] {
    if $bucket == null {
        print "エラー: バケット名を指定してください (--bucket オプション)"
        return false
    }
    
    print $"バケット「($bucket)」から「($file)」をダウンロードします"
    
    let download_result = (s3cmd get s3://$bucket/$file $output | complete)
    
    if $download_result.exit_code == 0 {
        print "ファイルのダウンロードに成功しました"
        print $download_result.stdout
        
        # 元のファイルと比較
        let original = (open $file | str trim)
        let downloaded = (open $output | str trim)
        
        if $original == $downloaded {
            print "元のファイルとダウンロードしたファイルの内容が一致しています"
            return true
        } else {
            print "警告: 元のファイルとダウンロードしたファイルの内容が一致していません"
            return false
        }
    } else {
        print "ファイルのダウンロードに失敗しました"
        print $download_result.stderr
        return false
    }
}

# クリーンアップ
def cleanup [--bucket(-b): string, --files(-f): list<string> = ["test-file.txt", "downloaded-file.txt"]] {
    print "クリーンアップを実行します"
    
    # ローカルのテストファイルを削除
    for file in $files {
        if ($file | path exists) {
            rm $file
            print $"ローカルファイル「($file)」を削除しました"
        }
    }
    
    # バケット内のファイルを削除（バケット名が指定されている場合）
    if $bucket != null {
        let delete_result = (s3cmd del s3://$bucket/test-file.txt | complete)
        if $delete_result.exit_code == 0 {
            print "バケット内のファイルを削除しました"
        } else {
            print "バケット内のファイル削除に失敗しました"
            print $delete_result.stderr
        }
    }
    
    print "クリーンアップ完了"
    return true
}

# メイン関数
export def main [
    --check-commands(-c),
    --create-bucket(-b): string,  # バケット名を指定
    --compartment-id: string,     # OCIコンパートメントID
    --namespace: string,          # OCIオブジェクトストレージNamespace
    --check-env(-e),
    --create-config(-f),
    --test-connection(-t),
    --upload(-u): string,         # アップロード先のバケット名
    --download(-d): string,       # ダウンロード元のバケット名
    --cleanup: string             # クリーンアップ対象のバケット名
] {
    if $check_commands {
        check_commands
    } else if $create_bucket != null {
        create_oci_bucket --name $create_bucket --compartment-id $compartment_id --namespace $namespace
    } else if $check_env {
        check_env_vars
    } else if $create_config {
        create_s3cfg
    } else if $test_connection {
        test_connection
    } else if $upload != null {
        upload_test_file --bucket $upload
    } else if $download != null {
        download_test_file --bucket $download
    } else if $cleanup != null {
        cleanup --bucket $cleanup
    } else {
        # デフォルトはコマンド確認
        check_commands
        
        print "\n使用方法:"
        print "  s3.nu --check-commands (-c)    : コマンドの確認"
        print "  s3.nu --create-bucket (-b) NAME [--compartment-id ID] [--namespace NS]: OCIバケットの作成"
        print "  s3.nu --check-env (-e)        : 環境変数の確認"
        print "  s3.nu --create-config (-f)    : s3cfg設定ファイルの作成"
        print "  s3.nu --test-connection (-t)  : S3接続テスト"
        print "  s3.nu --upload (-u) BUCKET    : テストファイルのアップロード"
        print "  s3.nu --download (-d) BUCKET  : テストファイルのダウンロード"
        print "  s3.nu --cleanup BUCKET        : クリーンアップ"
    }
}
