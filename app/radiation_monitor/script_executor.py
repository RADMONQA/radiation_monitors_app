import subprocess
import os
import shlex
from pathlib import Path
from typing import Optional, Dict, Union, List
import logging
import pkg_resources
import stat
import signal

logger = logging.getLogger(__name__)


class ScriptExecutionError(Exception):
    """Custom exception for script execution errors."""

    def __init__(self,
                 message: str,
                 return_code: int = -1):
        self.message = message
        self.return_code = return_code
        super().__init__(self.message)


def execute_script(
    script_name: str,
    env_vars: Optional[Dict[str, str]] = None,
    timeout: int = 3600,
    working_dir: Optional[Union[str, Path]] = None,
    args: Optional[List[str]] = None
) -> None:
    """
    Safely execute a bash script from the package.

    Args:
        script_name: Name of the script (with or without .sh extension)
        env_vars: Dictionary of environment variables to pass to the script
        timeout: Maximum execution time in seconds
        working_dir: Working directory for script execution
        args: List of additional arguments to pass to the script

    Returns:
        Tuple[str, str]: stdout and stderr from the script

    Raises:
        ScriptExecutionError: If script execution fails
        FileNotFoundError: If script doesn't exist
        PermissionError: If script isn't executable
    """

    # Normalize script name
    if not script_name.endswith('.sh'):
        script_name += '.sh'

    # Get script path from package resources
    scripts_dir = pkg_resources.resource_filename(
        'radiation_monitor', '../scripts')
    script_path = Path(scripts_dir).resolve()

    # Look for the script recursively
    script_file = None
    for path in script_path.rglob(script_name):
        if path.is_file():
            script_file = path
            break

    if not script_file:
        raise FileNotFoundError(
            f"Script {script_name} not found in package")

    # Verify script permissions and fix if needed
    current_perms = os.stat(script_file).st_mode
    if not current_perms & stat.S_IXUSR:
        logger.warning(
            f"Script {script_name} not executable, fixing permissions")
        os.chmod(script_file, current_perms | stat.S_IXUSR)

    # Prepare environment
    script_env = os.environ.copy()
    if env_vars:
        script_env.update(env_vars)

    # Prepare command
    cmd = [str(script_file)]
    if args:
        cmd.extend([shlex.quote(arg) for arg in args])

    # Prepare working directory
    work_dir = Path(working_dir).resolve(
    ) if working_dir else script_file.parent

    logger.debug(f"Executing script: {' '.join(cmd)}")
    logger.debug(f"Working directory: {work_dir}")
    logger.debug(f"Custom environment variables: {env_vars}")

    try:
        # Execute script using Popen with its own process group
        process = subprocess.Popen(
            cmd,
            env=script_env,
            cwd=work_dir,
            stdout=None,  # Stream to terminal
            stderr=None,  # Stream to terminal
            text=True,
            shell=False,  # More secure
            preexec_fn=os.setsid  # Create new process group
        )

        process.wait(timeout=timeout)

        # Check return code
        if process.returncode != 0:
            raise ScriptExecutionError(
                f"Script {script_name} failed with return code {process.returncode}",
                return_code=process.returncode
            )

    except subprocess.TimeoutExpired:
        # Kill the entire process group
        os.killpg(process.pid, signal.SIGKILL)
        process.wait()  # Ensure process is fully terminated
        raise ScriptExecutionError(
            f"Script {script_name} timed out after {timeout} seconds"
        )
    except (OSError, subprocess.SubprocessError) as e:
        # Kill the entire process group
        os.killpg(process.pid, signal.SIGKILL)
        process.wait()  # Ensure process is fully terminated
        raise ScriptExecutionError(
            f"Failed to execute script {script_name}: {str(e)}")
    except KeyboardInterrupt:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait()  # Ensure process is fully terminated
        raise KeyboardInterrupt
