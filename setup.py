#!/usr/bin/env python3
"""
Setup script to initialize data files from templates.
Run this before starting the bot on a new deployment.
"""
import os
import shutil

# List of data files and their templates
DATA_FILES = {
    'giveaway_config.json': 'giveaway_config_template.json',
    'timechannel_config.json': 'timechannel_config_template.json',
    'welcomer_config.json': 'welcomer_config_template.json',
    'warnings.json': 'warnings_template.json',
    'userphone_stats.json': 'userphone_stats_template.json',
}

def setup_data_files():
    """Create data files from templates if they don't exist"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    for data_file, template_file in DATA_FILES.items():
        data_path = os.path.join(script_dir, data_file)
        template_path = os.path.join(script_dir, template_file)
        
        # Only create if the data file doesn't exist
        if not os.path.exists(data_path):
            if os.path.exists(template_path):
                shutil.copy(template_path, data_path)
                print(f"✓ Created {data_file} from template")
            else:
                print(f"⚠ Warning: Template {template_file} not found")
        else:
            print(f"→ {data_file} already exists, skipping")

if __name__ == '__main__':
    print("Setting up data files...")
    setup_data_files()
    print("Setup complete!")
