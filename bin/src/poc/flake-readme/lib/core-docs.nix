# Core documentation functions (system-independent)
{ lib, self }:

let
  # Syntax check using nix-instantiate --parse
  checkSyntax = filePath:
    let
      parseResult = builtins.tryEval (
        derivation {
          name = "syntax-check";
          system = "x86_64-linux";
          builder = "/bin/sh";
          args = [
            "-c"
            ''nix-instantiate --parse "${filePath}" >/dev/null 2>&1 && echo "valid" || echo "invalid"''
          ];
        }
      );
    in
    if parseResult.success then
      # Use a simpler approach: try to read and parse the file structure
      let
        content = builtins.readFile filePath;
        # Basic syntax validation - check for common syntax issues
        hasBalancedBraces = 
          let 
            chars = lib.stringToCharacters content;
            count = builtins.foldl' (acc: char:
              if char == "{" then acc + 1
              else if char == "}" then acc - 1
              else acc
            ) 0 chars;
          in count == 0;
        hasBalancedParens =
          let 
            chars = lib.stringToCharacters content;
            count = builtins.foldl' (acc: char:
              if char == "(" then acc + 1
              else if char == ")" then acc - 1
              else acc
            ) 0 chars;
          in count == 0;
        hasBalancedBrackets =
          let 
            chars = lib.stringToCharacters content;
            count = builtins.foldl' (acc: char:
              if char == "[" then acc + 1
              else if char == "]" then acc - 1
              else acc
            ) 0 chars;
          in count == 0;
      in
      {
        isValid = hasBalancedBraces && hasBalancedParens && hasBalancedBrackets;
        error = if !(hasBalancedBraces && hasBalancedParens && hasBalancedBrackets) 
               then "Syntax error: unbalanced delimiters"
               else null;
      }
    else
      { isValid = false; error = "Cannot read file for syntax check"; };

  # Default ignore patterns  
  defaultIgnore = name: type:
    builtins.elem name [
      ".git" ".direnv" "node_modules" "result" "dist" "target" ".cache"
    ] || (name == "examples" && type == "directory");  # Ignore examples/ to isolate invalid samples

  # Recursively collect documentation files (readme.nix only)
  collectDocsRecursive = { root, names, ignore, path ? "" }:
    let
      dir = if path == "" then root else "${root}/${path}";
      entries = builtins.readDir dir;
      
      processEntry = name: type:
        let
          relativePath = if path == "" then name else "${path}/${name}";
          fullPath = "${dir}/${name}";
        in
        if ignore name type then
          {}
        else if type == "directory" then
          collectDocsRecursive {
            inherit root names ignore;
            path = relativePath;
          }
        else if type == "regular" && builtins.elem name names then
          let
            syntaxCheck = checkSyntax fullPath;
            imported = if syntaxCheck.isValid 
                      then builtins.tryEval (import fullPath)
                      else { success = false; value = null; };
          in
          { "${if path == "" then "." else path}" = {
              file = name;
              content = if !syntaxCheck.isValid then {
                         _syntaxError = true;
                         _errorPath = fullPath;
                         _syntaxErrorType = "parse";
                         _syntaxErrorMessage = syntaxCheck.error;
                         description = "Syntax error in readme.nix: ${syntaxCheck.error}";
                         goal = ["N/A (syntax error)"];
                         nonGoal = ["N/A (syntax error)"];
                         meta = {};
                         output = {};
                       }
                       else if imported.success 
                       then imported.value 
                       else { 
                         _syntaxError = true;
                         _errorPath = fullPath;
                         _syntaxErrorType = "evaluation";
                         description = "Evaluation error in readme.nix";
                         goal = ["N/A (evaluation error)"];
                         nonGoal = ["N/A (evaluation error)"];
                         meta = {};
                         output = {};
                       };
            };
          }
        else
          {};
      
      collected = lib.mapAttrsToList processEntry entries;
    in
    lib.foldl' lib.recursiveUpdate {} collected;

  # List directories and whether they have readme.nix
  listDirsRecursive = { root, ignore, path ? "" }:
    let
      dir = if path == "" then root else "${root}/${path}";
      entries = builtins.readDir dir;
      thisPath = if path == "" then "." else path;
      hasReadme = entries ? "readme.nix" && entries."readme.nix" == "regular";
      names = builtins.attrNames entries;
      # isDocumentable tracks which directories contain .nix files (fact collection only)
      # This fact is preserved for future policy extensions but not used in current missing detection
      isDocumentable = lib.any (n: entries.${n} == "regular" && n != "readme.nix" && lib.hasSuffix ".nix" n) names;
      here = { "${thisPath}" = { inherit hasReadme isDocumentable; }; };
      children = lib.mapAttrsToList (name: type:
        if ignore name type || type != "directory" then {}
        else listDirsRecursive { inherit root ignore; path = if path == "" then name else "${path}/${name}"; }
      ) entries;
    in
    lib.foldl' lib.recursiveUpdate here children;

  listMissingReadmes = { root, ignore, missingIgnoreExtra ? null }:
    let
      dirs = listDirsRecursive { inherit root ignore; };
      # 必須判定用のignore関数（missingIgnoreExtraが指定されていれば追加適用）
      missingIgnore = if missingIgnoreExtra == null 
                     then ignore 
                     else (name: type: ignore name type || missingIgnoreExtra name type);
      
      # 必須判定でmissingIgnoreを適用
      missing = lib.mapAttrsToList (p: v: 
        let
          # パスからディレクトリ名を取得（"." は "." のまま、"foo/bar" は "bar"）
          dirName = if p == "." then "." else builtins.baseNameOf p;
          # パスの親ディレクトリを取得してtypeを"directory"として判定
          shouldIgnore = missingIgnore dirName "directory";
        in
        # Policy: All directories require readme.nix unless explicitly ignored
        # Architectural change: Removed isDocumentable from policy to achieve SRP separation
        if (!v.hasReadme) && (!shouldIgnore) then p else null
      ) dirs;
    in
    lib.filter (x: x != null) missing;

  # Normalize a document to v1 schema
  normalizeDoc = { path, doc }:
    let
      isSyntaxError = doc ? _syntaxError && doc._syntaxError;
      isV1 = doc ? description && doc ? goal && doc ? nonGoal;
      isLegacy = doc ? description || doc ? purpose || doc ? contains || doc ? depends;
    in
    if isSyntaxError then
      {
        schemaVersion = 1;
        description = doc.description;
        goal = doc.goal;
        nonGoal = doc.nonGoal;
        meta = doc.meta;
        output = doc.output;
        source = {
          schema = "syntax-error";
          inherit path;
          errorPath = doc._errorPath;
        };
        _syntaxError = true;
        _errorPath = doc._errorPath;
      }
    else if isV1 then
      let
        allowedTop = ["description" "goal" "nonGoal" "meta" "output"];
        extra = lib.filterAttrs (k: v: !(builtins.elem k allowedTop)) doc;
      in
      {
        schemaVersion = 1;
        description = doc.description;
        goal = doc.goal or [];
        nonGoal = doc.nonGoal or [];
        meta = doc.meta or {};
        output = doc.output or {};
        source = {
          schema = "v1";
          inherit path;
        };
      } // (if extra != {} then { inherit extra; } else {})
    else if isLegacy then
      {
        schemaVersion = 1;
        description = doc.description or doc.purpose or "No description";
        goal = doc.goal or (if doc ? contains then doc.contains else []);
        nonGoal = doc.nonGoal or [];
        meta = doc.meta or {};
        output = doc.output or {};
        source = {
          schema = "legacy";
          inherit path;
        };
        extra = lib.filterAttrs (n: v: 
          !builtins.elem n ["description" "goal" "nonGoal" "contains"]
        ) doc;
      }
    else
      {
        schemaVersion = 1;
        description = "Invalid document format";
        goal = [];
        nonGoal = [];
        meta = doc.meta or {};
        output = doc.output or {};
        source = {
          schema = "unknown";
          inherit path;
        };
      };

  # TODO(ignore-refinement): collectIgnore と missingIgnore を分離する
  # - 目的: docs/examples/ を「収集するが必須対象外」にする柔軟性
  # - deadline: 必要時（docs/examples/ 配下の readme.nix を収集したくなったとき）
  # - owner: @project-maintainers
  #
  # 設計案:
  # - collectIgnore: 収集から除外（現在の ignore 相当）
  # - missingIgnore: 必須対象から除外（新設）
  # - index関数に { collectIgnore, missingIgnore } オプションを追加
  # - flake-module.nix も ignoreExtra を missingIgnore に配線
  # - 例: examples/ は collectIgnore=false, missingIgnore=true で「収集するが必須ではない」が可能
  # - 現状: examples/ は defaultIgnore で完全除外（異常系サンプル隔離のため）

  # TODO(docs): 出力突合チェックを導入するか決定する
  # - options: keep(drift check) | drop(型検証のみ)  
  # - deadline: 2025-01-15（2週間目安）
  # - owner: @project-maintainers
  # 
  # If keep:
  # - scope: flake output名のみ（packages/apps/modules/overlays/devShells）
  # - mode: WARN by default（環境変数 READMEX_STRICT=true でfail）
  # - metrics: 2週間で誤検知<5%、検出ドリフト>0件なら正式採用
  #
  # Defer:
  # - any-language output（関数/ファイル粒度）はプラグイン設計が固まるまで見送り（AST/LSPが要る）

  # TODO(flake-parts): flake-partsモジュール化を実装する
  # - 目的: 各プロジェクトが perSystem.checks.readme を有効化するだけで必須化と検証を利用可能に
  # - deadline: 2025-02-01（4週間目安）
  # - owner: @project-maintainers
  #
  # 実装内容:
  # - flakeModules.readme を提供
  # - options:
  #   - perSystem.readme.enable = mkEnableOption
  #   - perSystem.readme.systems = [ ... ]
  #   - perSystem.readme.policy = { requireAllKeys = false; ... }
  # - perSystem.checks.readme を runCommand + jq で配線、packages.docs-report も自動生成
  #
  # 導入例:
  # inputs.flake-parts, inputs.flake-readme,
  # outputs = flake-parts.lib.mkFlake { imports = [ flake-readme.flakeModules.readme ]; }
  #
  # 留意点: flake-parts 未採用のリポにも落とせるよう、従来の「生のflake例」もREADMEに保持

  # Validate a normalized document
  validateDoc = { path, doc }:
    let
      # helper: ensure list of strings
      isListOfStrings = xs: builtins.isList xs && lib.all builtins.isString xs;

      allowedOutputKeys = ["packages" "apps" "modules" "overlays" "devShells"];

      # TODO: ここにflake出力との突合処理を追加予定
      # flakeOutputs = getFlakeOutputs path;
      # driftCheck = compareDrift doc.output flakeOutputs;
      
      # Check for syntax errors first
      syntaxErrors = if (doc ? _syntaxError && doc._syntaxError) 
                    then [(
                      if (doc ? _syntaxErrorType && doc._syntaxErrorType == "parse")
                      then "Syntax error at ${doc._errorPath or path}: ${doc._syntaxErrorMessage or "unknown parse error"}"
                      else if (doc ? _syntaxErrorType && doc._syntaxErrorType == "evaluation")
                      then "Evaluation error at ${doc._errorPath or path}"
                      else "Import failed at ${doc._errorPath or path}"
                    )] 
                    else [];
      
      # Skip validation if syntax error occurred
      validationErrors = if syntaxErrors != [] then [] else [
        (if doc.description == "" then "Empty description at ${path}" else null)
        (if !builtins.isList doc.goal then "goal must be an array at ${path}" else null)
        (if !builtins.isList doc.nonGoal then "nonGoal must be an array at ${path}" else null)
        (if doc.goal == [] then "Empty goal array at ${path}" else null)
        (if doc.nonGoal == [] then "Empty nonGoal array at ${path}" else null)
        (if !(doc ? meta) then "Missing meta at ${path}" else null)
        (if (doc ? meta) && !builtins.isAttrs doc.meta then "meta must be an attrset at ${path}" else null)
        (if !(doc ? output) then "Missing output at ${path}" else null)
        (if (doc ? output) && !builtins.isAttrs doc.output then "output must be an attrset at ${path}" else null)
        (if (doc ? output && doc.output ? packages && !isListOfStrings doc.output.packages) then "output.packages must be a list of strings at ${path}" else null)
        (if (doc ? output && doc.output ? apps && !isListOfStrings doc.output.apps) then "output.apps must be a list of strings at ${path}" else null)
        (if (doc ? output && doc.output ? modules && !isListOfStrings doc.output.modules) then "output.modules must be a list of strings at ${path}" else null)
        (if (doc ? output && doc.output ? overlays && !isListOfStrings doc.output.overlays) then "output.overlays must be a list of strings at ${path}" else null)
        (if (doc ? output && doc.output ? devShells && !isListOfStrings doc.output.devShells) then "output.devShells must be a list of strings at ${path}" else null)
      ];
      
      errors = syntaxErrors ++ (lib.filter (x: x != null) validationErrors);
      
      # Skip warnings if syntax error occurred
      warnings = if syntaxErrors != [] then [] else []
        ++ (if builtins.stringLength doc.description > 80 
            then ["Description exceeds 80 characters at ${path}"] 
            else [])
        ++ (if doc.source.schema == "legacy" 
            then ["Using legacy schema at ${path}, consider migrating to v1"] 
            else [])
        ++ (if doc ? extra && doc.extra != {} 
            then ["Unknown keys found at ${path}: ${toString (builtins.attrNames doc.extra)}"] 
            else [])
        ++ (if (doc ? output) then
              let unknown = lib.filter (k: !builtins.elem k allowedOutputKeys) (builtins.attrNames doc.output);
              in if unknown != [] then ["Unknown output keys at ${path}: ${toString unknown}"] else []
            else []);
    in
    { inherit errors warnings; };

  # Collect raw documents from filesystem
  collect = { root ? (if self ? outPath then self.outPath else ./.), names ? [ "readme.nix" ], ignore ? defaultIgnore }:
    let
      collected = collectDocsRecursive { inherit root names ignore; };
      warnings = [];
    in
    {
      byPath = lib.mapAttrs (path: entry: entry.content) collected;
      inherit warnings;
    };

  # Create a complete index with normalized documents
  index = { root ? (if self ? outPath then self.outPath else ./.), names ? [ "readme.nix" ], ignore ? null, missingIgnoreExtra ? null }:
    let
      actualIgnore = if ignore == null then defaultIgnore else ignore;
      collected = collect { inherit root names; ignore = actualIgnore; };
      normalized = lib.mapAttrs (path: doc: normalizeDoc { inherit path doc; }) collected.byPath;
      missingReadmes = listMissingReadmes { 
        inherit root; 
        ignore = actualIgnore; 
        inherit missingIgnoreExtra;
      };
      reports = lib.mapAttrs (path: doc: validateDoc { inherit path doc; }) normalized;
      allErrors = lib.concatMap (p: (reports.${p}.errors)) (builtins.attrNames reports);
      allWarnings = lib.concatMap (p: (reports.${p}.warnings)) (builtins.attrNames reports);
    in
    {
      schemaVersion = 1;
      docs = normalized;
      warnings = collected.warnings ++ allWarnings;
      missingReadmes = missingReadmes;
      reports = reports;
      errorCount = builtins.length allErrors + (builtins.length missingReadmes);
      warningCount = builtins.length (collected.warnings ++ allWarnings);
    };

in
{
  inherit collect normalizeDoc validateDoc index;
  # API minimized to 4 core functions (SOLID principle)
  # _internal exposure removed - no external dependencies confirmed
}
