import asyncio
import os
import sys
import hashlib
import logging

# Setup Path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.uploader_monitored import upload_video_monitored
from unittest.mock import patch, MagicMock

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("IntegrityTest")

async def test_integrity():
    # Mock launch_browser to fail fast
    with patch('core.uploader_monitored.launch_browser', side_effect=Exception("Mock Browser Launch Stopped Here")):
        # 1. Create Dummy Video File
        test_file = "test_integrity_video.mp4"
        with open(test_file, "wb") as f:
            f.write(b"dummy_video_content_for_integrity_check")
        
        # 2. Calculate Real Checksum
        hasher = hashlib.md5()
        with open(test_file, "rb") as f:
            hasher.update(f.read())
        real_md5 = hasher.hexdigest()
        
        logger.info(f"Generated Test File: {test_file}")
        logger.info(f"Real MD5: {real_md5}")
        
        # 3. Test Case A: Valid Checksum (Should Proceed - failure at mock launch expected)
        logger.info("\n--- TEST CASE A: Valid Checksum ---")
        try:
            result = await upload_video_monitored(
                session_name="dummy_session",
                video_path=test_file,
                caption="test",
                md5_checksum=real_md5,
                enable_monitor=False
            )
        except Exception as e:
            if "Mock Browser Launch Stopped Here" in str(e):
                logger.info("✅ TEST CASE A PASSED: Integrity Check OK (Proceeded to browser launch)")
            else:
                logger.error(f"❌ TEST CASE A FAILED: Unexpected error: {e}")
            
        # 4. Test Case B: Invalid Checksum (Should fail IMMEDIATELY, before mock launch)
        logger.info("\n--- TEST CASE B: Invalid Checksum ---")
        fake_md5 = "00000000000000000000000000000000"
        result_b = await upload_video_monitored(
            session_name="dummy_session",
            video_path=test_file,
            caption="test",
            md5_checksum=fake_md5,
            enable_monitor=False
        )
        
        if result_b["status"] == "error" and "MD5 Mismatch" in result_b["message"]:
            logger.info("✅ TEST CASE B PASSED: Invalid Checksum correctly rejected.")
        else:
            logger.error(f"❌ TEST CASE B FAILED: Invalid Checksum was NOT rejected. Result: {result_b}")

        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)

if __name__ == "__main__":
    asyncio.run(test_integrity())
