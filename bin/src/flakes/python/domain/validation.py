#!/usr/bin/env python3
"""
検証ロジック

ツール実行結果の検証とビジネスルールの適用を行います。
"""

import json
from typing import Dict, Any, List, TypedDict, Optional


class ValidationIssue(TypedDict):
    """検証で発見された問題"""
    severity: str  # error, warning, info
    message: str
    file: Optional[str]
    line: Optional[int]
    column: Optional[int]


class AnalysisResult(TypedDict):
    """分析結果"""
    valid: bool
    issues: List[ValidationIssue]
    summary: Dict[str, int]  # error_count, warning_count, etc.


def validate_pyright_output(output: str) -> AnalysisResult:
    """
    pyrightの出力を検証し、型エラーを分析
    
    Args:
        output: pyrightの標準出力
        
    Returns:
        AnalysisResult: 分析結果
    """
    issues: List[ValidationIssue] = []
    error_count = 0
    warning_count = 0
    info_count = 0
    
    try:
        # JSON出力の場合
        if output.strip().startswith('{'):
            data = json.loads(output)
            diagnostics = data.get('diagnostics', [])
            
            for diag in diagnostics:
                severity = diag.get('severity', 'error')
                issue = ValidationIssue(
                    severity=severity,
                    message=diag.get('message', ''),
                    file=diag.get('file', {}).get('uri'),
                    line=diag.get('range', {}).get('start', {}).get('line'),
                    column=diag.get('range', {}).get('start', {}).get('character'),
                )
                issues.append(issue)
                
                if severity == 'error':
                    error_count += 1
                elif severity == 'warning':
                    warning_count += 1
                else:
                    info_count += 1
        else:
            # テキスト出力の解析
            lines = output.strip().split('\n')
            for line in lines:
                if ' - error:' in line:
                    error_count += 1
                    issues.append(ValidationIssue(
                        severity='error',
                        message=line.split(' - error:')[1].strip(),
                        file=None,
                        line=None,
                        column=None,
                    ))
                elif ' - warning:' in line:
                    warning_count += 1
                    issues.append(ValidationIssue(
                        severity='warning',
                        message=line.split(' - warning:')[1].strip(),
                        file=None,
                        line=None,
                        column=None,
                    ))
    except (json.JSONDecodeError, KeyError) as e:
        issues.append(ValidationIssue(
            severity='error',
            message=f'Failed to parse pyright output: {str(e)}',
            file=None,
            line=None,
            column=None,
        ))
        error_count += 1
    
    return AnalysisResult(
        valid=error_count == 0,
        issues=issues,
        summary={
            'error_count': error_count,
            'warning_count': warning_count,
            'info_count': info_count,
            'total_count': len(issues),
        }
    )


def validate_pytest_output(output: str, json_report: Optional[str] = None) -> AnalysisResult:
    """
    pytestの出力を検証し、テスト結果を分析
    
    Args:
        output: pytestの標準出力
        json_report: pytest-json-reportの出力（オプション）
        
    Returns:
        AnalysisResult: 分析結果
    """
    issues: List[ValidationIssue] = []
    passed = 0
    failed = 0
    skipped = 0
    errors = 0
    
    if json_report:
        try:
            data = json.loads(json_report)
            summary = data.get('summary', {})
            passed = summary.get('passed', 0)
            failed = summary.get('failed', 0)
            skipped = summary.get('skipped', 0)
            errors = summary.get('error', 0)
            
            # 失敗したテストの詳細を取得
            for test in data.get('tests', []):
                if test.get('outcome') == 'failed':
                    issues.append(ValidationIssue(
                        severity='error',
                        message=test.get('call', {}).get('longrepr', 'Test failed'),
                        file=test.get('nodeid', '').split('::')[0],
                        line=None,
                        column=None,
                    ))
        except (json.JSONDecodeError, KeyError):
            pass
    
    # テキスト出力からの解析（フォールバック）
    if not issues and 'FAILED' in output:
        lines = output.split('\n')
        for i, line in enumerate(lines):
            if 'FAILED' in line:
                issues.append(ValidationIssue(
                    severity='error',
                    message=line.strip(),
                    file=None,
                    line=None,
                    column=None,
                ))
                failed += 1
    
    return AnalysisResult(
        valid=failed == 0 and errors == 0,
        issues=issues,
        summary={
            'passed': passed,
            'failed': failed,
            'skipped': skipped,
            'errors': errors,
            'total': passed + failed + skipped + errors,
        }
    )


def validate_ruff_output(output: str) -> AnalysisResult:
    """
    ruffの出力を検証し、リンティング結果を分析
    
    Args:
        output: ruffの標準出力
        
    Returns:
        AnalysisResult: 分析結果
    """
    issues: List[ValidationIssue] = []
    error_count = 0
    
    # ruffの出力形式: filename:line:col: code message
    lines = output.strip().split('\n')
    for line in lines:
        line = line.strip()
        if not line:  # 空行をスキップ
            continue
        if ':' in line and not line.startswith('Found'):
            parts = line.split(':', 3)  # ファイル名:行:列: メッセージ
            if len(parts) >= 4:
                # メッセージ部分をコードと説明に分割
                msg_parts = parts[3].strip().split(' ', 1)
                code = msg_parts[0] if msg_parts else ''
                message = msg_parts[1] if len(msg_parts) > 1 else parts[3].strip()
                
                issues.append(ValidationIssue(
                    severity='warning',  # ruffの問題は基本的にwarning扱い
                    message=f"{code}: {message}" if code else message,
                    file=parts[0],
                    line=int(parts[1]) if parts[1].isdigit() else None,
                    column=int(parts[2]) if parts[2].isdigit() else None,
                ))
                error_count += 1
    
    return AnalysisResult(
        valid=error_count == 0,
        issues=issues,
        summary={
            'error_count': 0,
            'warning_count': error_count,
            'info_count': 0,
            'total_count': error_count,
        }
    )