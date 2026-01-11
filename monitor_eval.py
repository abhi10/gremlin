#!/usr/bin/env python3
"""Monitor eval progress and report milestones."""
import time
import sys
from pathlib import Path

output_file = Path("/var/folders/hf/m8jm_tcx7kg3sgnzg710198m0000gn/T/claude/-Users-abhishekrajuchamarthi-Dropbox-Mac-Documents-workspace-personal-gremlin/tasks/bf5b92a.output")
total_cases = 54
milestone_50 = 27
notified_50 = False
last_count = 0

while True:
    if output_file.exists():
        content = output_file.read_text()
        completed = content.count("Overall Winner:")
        
        # Report progress
        if completed != last_count:
            print(f"Progress: {completed}/{total_cases} cases completed ({completed*100//total_cases}%)")
            last_count = completed
        
        # 50% milestone
        if completed >= milestone_50 and not notified_50:
            print(f"\n🎯 MILESTONE: 50% Complete ({completed}/{total_cases} cases)")
            notified_50 = True
        
        # 100% milestone
        if completed >= total_cases:
            print(f"\n✅ COMPLETE: All {total_cases} cases finished!")
            
            # Check for errors in summary
            if "Overall Summary" in content:
                summary_start = content.rfind("Overall Summary")
                summary = content[summary_start:]
                print("\n" + "="*50)
                print(summary[:500])
            
            sys.exit(0)
    
    time.sleep(30)  # Check every 30 seconds
