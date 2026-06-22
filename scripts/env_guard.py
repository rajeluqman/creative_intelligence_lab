"""Fail-closed env guard (mirror of pharma gym_guard). Import + call assert_safe() in any
runner that touches S3, so a misconfigured env aborts instead of hitting the wrong bucket."""
import os
import sys


def assert_safe():
    bucket = os.getenv("S3_BUCKET", "")
    if not bucket:
        sys.exit("env_guard: S3_BUCKET unset - refusing to run.")
    # Extend: in a gym/incubator context require a throwaway bucket + fake creds + local endpoint.


if __name__ == "__main__":
    assert_safe()
    print("env_guard: ok")
