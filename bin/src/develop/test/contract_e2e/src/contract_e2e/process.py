"""Process execution functions"""

import subprocess
import json
from typing import Dict, Any, Tuple, Optional
from .types import ProcessError, ParseError


def execute_subprocess(
    executable: str,
    input_data: Dict[str, Any],
    timeout: Optional[int] = None
) -> Tuple[Optional[Dict[str, Any]], Optional[ProcessError], Optional[ParseError]]:
    """Execute subprocess with JSON input/output
    
    Returns: (output_data, process_error, parse_error)
    """
    try:
        result = subprocess.run(
            executable,
            shell=True,
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        if result.returncode != 0:
            return None, ProcessError(
                type="process_error",
                exit_code=result.returncode,
                stderr=result.stderr,
                timeout=False
            ), None
        
        # Try to parse output as JSON
        try:
            output = json.loads(result.stdout.strip())
            return output, None, None
        except json.JSONDecodeError as e:
            return None, None, ParseError(
                type="parse_error",
                output=result.stdout,
                error=str(e)
            )
            
    except subprocess.TimeoutExpired:
        return None, ProcessError(
            type="process_error",
            exit_code=-1,
            stderr="Process timed out",
            timeout=True
        ), None
    except Exception as e:
        return None, ProcessError(
            type="process_error",
            exit_code=-1,
            stderr=str(e),
            timeout=False
        ), None