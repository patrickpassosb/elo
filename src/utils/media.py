import os
import requests
import tempfile
import logging
from contextlib import contextmanager
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config import settings
from logging_config import logger
from exceptions import MediaError

@contextmanager
def temporary_file(suffix: str = "") -> str:
    """Create a temporary file that is automatically cleaned up.
    
    Args:
        suffix (str): The file extension/suffix.
        
    Yields:
        str: The path to the temporary file.
    """
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)  # Close the low-level descriptor
    try:
        yield path
    finally:
        try:
            os.remove(path)
            logger.debug(f"Temporary file removed: {path}")
        except OSError:
            pass

@retry(retry=retry_if_exception_type(MediaError),
       wait=wait_exponential(multiplier=1, min=2, max=10),
       stop=stop_after_attempt(3),
       reraise=True)
def download_media(media_url: str, file_extension: str) -> str:
    """Download media from a URL and save it to a temporary file.
    
    Args:
        media_url (str): The URL to download from.
        file_extension (str): The extension for the saved file.
        
    Returns:
        str: The path to the downloaded temporary file.
        
    Raises:
        MediaError: If the download fails.
    """
    try:
        account_sid = settings.twilio_account_sid
        auth_token = settings.twilio_auth_token
        
        # Use auth only if Twilio creds are present (though this function might be used for other URLs too)
        auth = (account_sid, auth_token) if account_sid and auth_token else None
        
        response = requests.get(media_url, auth=auth, timeout=10)
        response.raise_for_status()
        
        with temporary_file(suffix=f".{file_extension}") as tmp_path:
            with open(tmp_path, "wb") as f:
                f.write(response.content)
            # Note: temporary_file cleans up on exit, but here we want to return the file.
            # This usage of temporary_file as a context manager to *create* a file we want to keep 
            # (until explicit cleanup) is slightly tricky. 
            # Actually, the original utils.py implementation returned the path from the context manager,
            # which means the file was deleted when the context manager exited!
            # WAIT. In the original code:
            # with temporary_file(...) as tmp_path:
            #    ... write ...
            #    return tmp_path 
            # This would return the path, BUT the `finally` block would run and delete it!
            # This looks like a BUG in the original code unless I misread it.
            # Let's re-read original utils.py.
            pass
            
        # Re-reading utils.py:
        # with temporary_file(suffix=f".{file_extension}") as tmp_path:
        #     with open(tmp_path, "wb") as f:
        #         f.write(response.content)
        #     return tmp_path
        # YES! The finally block runs on exit. The file is deleted before the function returns?
        # No, `return` inside `with` triggers `__exit__`. So the file is deleted.
        # The caller gets a path to a non-existent file.
        # This was a BUG in the code I inherited/reviewed.
        # I must fix this.
        
        # FIX: Don't use temporary_file context manager for files we want to return.
        # Use tempfile.mkstemp directly.
        
        fd, path = tempfile.mkstemp(suffix=f".{file_extension}")
        os.close(fd)
        with open(path, "wb") as f:
            f.write(response.content)
        return path

    except requests.RequestException as e:
        raise MediaError(f"Failed to download media: {e}") from e
    except Exception as e:
        raise MediaError(f"Unexpected error downloading media: {e}") from e

def cleanup_file(file_path: str) -> None:
    """Remove a temporary file if it exists.
    
    Args:
        file_path (str): Path to the file to remove.
    """
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            logger.debug(f"Removed temporary file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to remove temporary file {file_path}: {e}")
