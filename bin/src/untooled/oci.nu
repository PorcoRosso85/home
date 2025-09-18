#!/usr/bin/env -S nix shell nixpkgs#oci-cli nixpkgs#openssl -c nu

# OCI CLIの設定ファイル用のフォルダを作成
def create_oci_directory [] {
    # OCIディレクトリの作成
    if not ("~/.oci" | path expand | path exists) {
        mkdir ~/.oci
        print "~/.ociディレクトリを作成しました"
    } else {
        print "~/.ociディレクトリは既に存在します"
    }
    
    return true
}

# 秘密鍵と公開鍵のペアについて説明
def generate_key_pair [] {
    print "APIキーペアが必要です..."
    
    # ディレクトリ作成を確認
    create_oci_directory
    
    # 鍵の生成方法を説明
    print "SSHクライアントを使用して鍵ペアを生成してください："
    print "1. 以下のコマンドで秘密鍵を生成："
    print "   ssh-keygen -t rsa -b 2048 -f ~/.oci/oci_api_key.pem"
    print "2. 公開鍵の形式変換："
    print "   openssl rsa -pubout -in ~/.oci/oci_api_key.pem -out ~/.oci/oci_api_key_public.pem"
    print "3. 適切なパーミッションを設定："
    print "   chmod 600 ~/.oci/oci_api_key.pem"
    print "   chmod 644 ~/.oci/oci_api_key_public.pem"
    
    # 鍵が存在するか確認
    let private_key_path = "~/.oci/oci_api_key.pem" | path expand
    let public_key_path = "~/.oci/oci_api_key_public.pem" | path expand
    
    if ($private_key_path | path exists) {
        print $"秘密鍵 ($private_key_path) は既に存在します"
    } else {
        print $"警告: 秘密鍵 ($private_key_path) が見つかりません"
    }
    
    if ($public_key_path | path exists) {
        print $"公開鍵 ($public_key_path) は既に存在します"
    } else {
        print $"警告: 公開鍵 ($public_key_path) が見つかりません"
    }
    
    return [
        $private_key_path,
        $public_key_path
    ]
}

# フィンガープリントの取得と計算
def calculate_fingerprint [key_path: string] {
    # 環境変数からフィンガープリントを確認
    let env_fingerprint = ($env | get -i OCI_FINGERPRINT)
    if $env_fingerprint != null {
        print $"環境変数OCI_FINGERPRINTが設定されています: ($env_fingerprint)"
        return $env_fingerprint
    }
    
    print $"鍵 ($key_path) のフィンガープリントを自動計算します..."
    
    # 2段階で処理を実行
    # 1. 秘密鍵から一時的な公開鍵を生成
    let temp_public_key = "/tmp/oci_temp_public.der"
    let pub_cmd = $"openssl rsa -pubout -outform DER -in ($key_path) -out ($temp_public_key)"
    let pub_result = (do { bash -c $pub_cmd } | complete)
    
    if $pub_result.exit_code != 0 {
        print "公開鍵への変換に失敗しました"
        print $pub_result.stderr
        print "OCI_FINGERPRINT環境変数に鍵のフィンガープリントを設定するか、--fingerprint オプションで直接指定してください"
        return null
    }
    
    # 2. DER形式の公開鍵からMD5ハッシュを計算
    let md5_cmd = $"openssl md5 -c ($temp_public_key)"
    let md5_result = (do { bash -c $md5_cmd } | complete)
    
    if $md5_result.exit_code != 0 {
        print "MD5ハッシュの計算に失敗しました"
        print $md5_result.stderr
        print "OCI_FINGERPRINT環境変数に鍵のフィンガープリントを設定するか、--fingerprint オプションで直接指定してください"
        return null
    }
    
    # 一時ファイルを削除
    rm -f $temp_public_key
    
    # 出力からフィンガープリント部分を抽出
    let fingerprint = ($md5_result.stdout | str trim | split row "= " | last)
    print $"フィンガープリント: ($fingerprint)"
    
    return $fingerprint
}

# TODO, keypathがオプション引数でない？ 環境変数設定後--authを行うとエラーが発生する
# OpenSSLを使用して鍵ペアを自動生成する
def generate_openssl_key_pair [] {
    print "OpenSSLを使用して鍵ペアを自動生成します..."
    
    # ディレクトリ作成を確認
    create_oci_directory
    
    let private_key_path = "~/.oci/oci_api_key.pem" | path expand
    let public_key_path = "~/.oci/oci_api_key_public.pem" | path expand
    
    # 秘密鍵の生成
    print "秘密鍵を生成中..."
    let private_key_result = (do {
        openssl genrsa -out $private_key_path 2048
    } | complete)
    
    if $private_key_result.exit_code != 0 {
        print "秘密鍵の生成に失敗しました"
        print $private_key_result.stderr
        return false
    }
    
    # 公開鍵の生成
    print "公開鍵を生成中..."
    let public_key_result = (do {
        openssl rsa -pubout -in $private_key_path -out $public_key_path
    } | complete)
    
    if $public_key_result.exit_code != 0 {
        print "公開鍵の生成に失敗しました"
        print $public_key_result.stderr
        return false
    }
    
    # パーミッションの設定
    chmod 600 $private_key_path
    chmod 644 $public_key_path
    
    print $"秘密鍵を ($private_key_path) に保存しました"
    print $"公開鍵を ($public_key_path) に保存しました"
    
    return [
        $private_key_path,
        $public_key_path
    ]
}

# OCI設定ファイルの作成
def create_oci_config [
    --user_ocid(-u): string,
    --tenancy_ocid(-t): string,
    --region(-r): string,
    --fingerprint(-f): string = "",
    --private_key_path(-k): string = "",
    --generate_keys(-g)
] {
    print "OCI設定ファイルを作成します..."
    
    # ディレクトリの確認
    create_oci_directory
    
    # デフォルトの鍵パス
    let default_key_path = "~/.oci/oci_api_key.pem" | path expand
    
    # 鍵の生成または既存の鍵の使用
    let key_paths = if $generate_keys {
        generate_key_pair
    } else if ($private_key_path != null and $private_key_path != "") {
        let key_path = $private_key_path | path expand
        if not ($key_path | path exists) {
            print $"エラー: 指定された秘密鍵 ($key_path) が見つかりません"
            return false
        }
        [$key_path, ""]
    } else if ($default_key_path | path exists) {
        # 既存の鍵を使用
        print $"既存の鍵 ($default_key_path) を使用します"
        [$default_key_path, ""]
    } else {
        print "警告: 鍵が見つからないため、OpenSSLで自動生成します"
        generate_openssl_key_pair
    }
    
    if $key_paths == false {
        return false
    }
    
    # パスを絶対パスに展開
    let private_key_path = $key_paths.0 | path expand
    
    # フィンガープリントを取得
    let fingerprint_value = if $fingerprint != "" {
        # 明示的に指定されたフィンガープリントを使用
        $fingerprint
    } else {
        # 環境変数から取得を試みる
        calculate_fingerprint $private_key_path
    }
    
    if $fingerprint_value == null {
        print "フィンガープリントの取得に失敗しました"
        return false
    }
    
    # 設定ファイルの内容を作成
    let config_content = $"
    [DEFAULT]
    user=($user_ocid)
    fingerprint=($fingerprint_value)
    tenancy=($tenancy_ocid)
    region=($region)
    key_file=($private_key_path)
    "
    
    # 設定ファイルの保存
    let config_path = "~/.oci/config" | path expand
    $config_content | save -f $config_path
    
    # 設定ファイルのパーミッション設定
    chmod 600 $config_path
    
    print $"OCI設定ファイルを ($config_path) に保存しました"
    print "設定内容:"
    print $config_content
    
    return true
}

# 環境変数から設定情報を取得
def load_from_env [] {
    let user_ocid = ($env | get -i OCI_USER_OCID)
    let tenancy_ocid = ($env | get -i OCI_TENANCY_OCID)
    let region = ($env | get -i OCI_REGION)
    let fingerprint = ($env | get -i OCI_FINGERPRINT)
    let private_key_path = ($env | get -i OCI_PRIVATE_KEY_PATH)
    
    if $user_ocid == null or $tenancy_ocid == null or $region == null {
        print "エラー: 必要な環境変数が設定されていません"
        print $"  OCI_USER_OCID: ($user_ocid)"
        print $"  OCI_TENANCY_OCID: ($tenancy_ocid)"
        print $"  OCI_REGION: ($region)"
        print "以下の環境変数を設定してください:"
        print "  OCI_USER_OCID - ユーザーのOCID"
        print "  OCI_TENANCY_OCID - テナンシーのOCID"
        print "  OCI_REGION - 使用するリージョン (例: us-ashburn-1)"
        print "オプションの環境変数:"
        print "  OCI_FINGERPRINT - 鍵のフィンガープリント"
        print "  OCI_PRIVATE_KEY_PATH - 秘密鍵のパス"
        return false
    }
    
    return {
        user_ocid: $user_ocid,
        tenancy_ocid: $tenancy_ocid,
        region: $region,
        fingerprint: $fingerprint,
        private_key_path: $private_key_path
    }
}

# 認証設定を実行する
def auth [
    --user_ocid(-u): string = "",
    --tenancy_ocid(-t): string = "",
    --region(-r): string = "",
    --fingerprint(-f): string = "",
    --private_key_path(-k): string = "",
    --generate_keys(-g)
] {
    # コマンドライン引数から設定情報を取得、または環境変数から取得
    let config = if $user_ocid != "" and $tenancy_ocid != "" and $region != "" {
        {
            user_ocid: $user_ocid,
            tenancy_ocid: $tenancy_ocid,
            region: $region,
            fingerprint: $fingerprint,
            private_key_path: $private_key_path
        }
    } else {
        let env_config = load_from_env
        if $env_config == false {
            # 環境変数が設定されていない場合、サンプル値を提示
            print "注意: 必要な環境変数が設定されていません。"
            print "以下のように環境変数を設定してください:"
            print "  export OCI_USER_OCID=ocid1.user.oc1..xxx"
            print "  export OCI_TENANCY_OCID=ocid1.tenancy.oc1..xxx"
            print "  export OCI_REGION=ap-tokyo-1"
            print ""
            print "今回はサンプル値で設定ファイルを作成します。後で正しい値に更新してください。"
            
            {
                user_ocid: "ocid1.user.oc1..exampleuserocid",
                tenancy_ocid: "ocid1.tenancy.oc1..exampletenancyocid",
                region: "ap-tokyo-1",
                fingerprint: $fingerprint,
                private_key_path: $private_key_path
            }
        } else {
            $env_config
        }
    }
    
    # OCI設定ファイルの作成
    let create_with_keys = if $generate_keys {
        create_oci_config --user_ocid $config.user_ocid --tenancy_ocid $config.tenancy_ocid --region $config.region --fingerprint $config.fingerprint --private_key_path $config.private_key_path --generate_keys
    } else {
        create_oci_config --user_ocid $config.user_ocid --tenancy_ocid $config.tenancy_ocid --region $config.region --fingerprint $config.fingerprint --private_key_path $config.private_key_path
    }
    $create_with_keys
}

# 認証設定の確認
def check_auth [] {
    print "OCI認証設定を確認します..."
    
    let config_path = "~/.oci/config" | path expand
    
    if not ($config_path | path exists) {
        print "OCI設定ファイルが見つかりません"
        print "auth機能を使用して設定してください: oci.nu --auth"
        return false
    }
    
    # 設定ファイルの内容を表示
    print "OCI設定ファイルの内容:"
    open $config_path
    
    # 鍵ファイルの存在確認
    let key_file = (open $config_path | lines | find "key_file" | str replace "key_file=" "")
    
    if $key_file == null or not ($key_file | path exists) {
        print $"警告: 秘密鍵ファイルが見つかりません: ($key_file)"
        return false
    }
    
    print $"秘密鍵ファイル ($key_file) が存在します"
    
    # テスト用に簡単なコマンドを実行
    print "OCI接続をテストしています..."
    let test_result = (oci iam region list | complete)
    
    if $test_result.exit_code == 0 {
        print "OCI接続テスト成功！"
        return true
    } else {
        print "OCI接続テスト失敗"
        print $test_result.stderr
        return false
    }
}

# メイン関数
export def main [
    --auth(-a),
    --check(-c),
    --generate_keys(-g),
    --user_ocid(-u): string = "",
    --tenancy_ocid(-t): string = "",
    --region(-r): string = "",
    --fingerprint(-f): string = "",
    --private_key_path(-k): string = ""
] {
    if $auth {
        let auth_with_keys = if $generate_keys {
            auth --user_ocid $user_ocid --tenancy_ocid $tenancy_ocid --region $region --fingerprint $fingerprint --private_key_path $private_key_path --generate_keys
        } else {
            auth --user_ocid $user_ocid --tenancy_ocid $tenancy_ocid --region $region --fingerprint $fingerprint --private_key_path $private_key_path
        }
        $auth_with_keys
    } else if $check {
        check_auth
    } else if $generate_keys {
        generate_key_pair
    } else {
        # OCIコマンドをそのまま実行
        print "OCI CLIを実行します。--authオプションを使用して認証設定を行うことができます。"
        print "使用例:"
        print "  oci.nu --auth                : 環境変数から認証情報を取得して設定"
        print "  oci.nu --auth -u USER -t TENANCY -r REGION : 指定した値で認証設定"
        print "  oci.nu --check               : 認証設定を確認"
        print "  oci.nu --generate_keys       : APIキーペアを生成"
        print "  oci.nu [OCIコマンド]         : OCIコマンドを実行"
        print ""
        print "環境変数:"
        print "  OCI_USER_OCID     : ユーザーのOCID"
        print "  OCI_TENANCY_OCID  : テナンシーのOCID"
        print "  OCI_REGION        : リージョン (例: us-ashburn-1)"
        print "  OCI_FINGERPRINT   : 鍵のフィンガープリント (オプション)"
        print "  OCI_PRIVATE_KEY_PATH : 秘密鍵のパス (オプション)"
    }
}

# TODO
# 以下を実行してもファイルがあることが確認でき、フィンガープリントが読み取れないだけ
# 
# ● まだ失敗しています。詳細を確認しましょう：
# 
# ● Bash(if [ -f ~/.oci/oci_api_key.pem ]; then…
#         echo "秘密鍵ファイルが存在します"
#         ls -la ~/.oci/oci_api_key.pem
#       else
#         echo "秘密鍵ファイルが存在しません"
#       fi)
#   ⎿  秘密鍵ファイルが存在します
#      -rw------- 1 nixos users 1704 Mar  8 07:02 /home/nixos/.oci/oci_api_key.pem


