#!/usr/bin/env python
"""
Test runner for AI Fashion Advisor tests.

Usage:
    python run_tests.py [OPTIONS]

Options:
    --unit       Run unit tests only
    --integration Run integration tests only
    --e2e        Run end-to-end tests only
    --live       Run tests that require actual services to be running
    --all        Run all tests (default)
    --service=X  Run tests for a specific service (detection, style, feature, etc.)
    --help       Show this help message
"""

import os
import sys
import subprocess
from pathlib import Path


def run_test_command(args, test_type=None, service=None, live=False):
    """Run pytest with the specified arguments."""
    cmd = ["pytest", "-v"]
    
    # Add test type if specified
    marker_expression = []
    if test_type:
        marker_expression.append(test_type)
    
    # Add service marker if specified
    if service:
        marker_expression.append(service)
    
    # Add live marker if specified
    if live:
        marker_expression.append("live")
    
    if marker_expression:
        cmd.extend(["-m", " and ".join(marker_expression)])
    
    # Add other arguments
    cmd.extend(args)
    
    # Run the command
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd)


def main():
    """Parse arguments and run tests."""
    # Default to running all tests
    run_all = True
    run_unit = False
    run_integration = False
    run_e2e = False
    run_live = False
    service = None
    args = []
    
    # Parse arguments
    for arg in sys.argv[1:]:
        if arg == "--unit":
            run_unit = True
            run_all = False
        elif arg == "--integration":
            run_integration = True
            run_all = False
        elif arg == "--e2e":
            run_e2e = True
            run_all = False
        elif arg == "--live":
            run_live = True
            run_all = False
        elif arg == "--all":
            run_all = True
        elif arg.startswith("--service="):
            service = arg.split("=")[1]
        elif arg == "--help":
            print(__doc__)
            return
        else:
            args.append(arg)
    
    # Ensure we're in the tests directory
    os.chdir(Path(__file__).parent)
    
    # Run tests
    if run_all:
        run_test_command(args, service=service)
    else:
        if run_unit:
            run_test_command(args, "unit", service)
        if run_integration:
            run_test_command(args, "integration", service)
        if run_e2e:
            run_test_command(args, "e2e", service)
        if run_live:
            run_test_command(args, None, service, live=True)


if __name__ == "__main__":
    main() 