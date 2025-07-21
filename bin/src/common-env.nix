# 共通環境定義
{ pkgs }:
{
  # 統一されたPythonバージョン
  python = pkgs.python311;
  
  # 共通のPythonパッケージ
  commonPythonPackages = ps: with ps; [
    pytest
    numpy
    pandas
    pydantic
    kuzu
  ];
  
  # プロジェクト全体のPython環境
  pythonEnv = pkgs.python311.withPackages (ps: 
    (commonPythonPackages ps)
  );
}