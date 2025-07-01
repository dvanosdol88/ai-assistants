#!/usr/bin/env python3
"""
Jules Handoff Automation Runner

This script implements the handoff poller for AI assistant communication.
It reads instructions from shared/claude-to-jules-message.md and writes
results to shared/jules-to-cc.md based on the schema defined in shared/schema.md.

Usage:
    python jules_runner.py [--check-once]
"""

import os
import sys
import time
import json
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

class HandoffPoller:
    def __init__(self, workspace_path: str):
        self.workspace = Path(workspace_path)
        self.shared_dir = self.workspace / "shared"
        self.input_file = self.shared_dir / "claude-to-jules-message.md"
        self.output_file = self.shared_dir / "jules-to-cc.md"
        self.schema_file = self.shared_dir / "schema.md"
        
        # Ensure shared directory exists
        self.shared_dir.mkdir(exist_ok=True)
    
    def read_message(self) -> Optional[Dict[str, Any]]:
        """Read and parse handoff message from Claude to Jules"""
        if not self.input_file.exists():
            return None
            
        try:
            with open(self.input_file, 'r') as f:
                content = f.read()
            
            # Parse YAML frontmatter if present
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    yaml_content = parts[1].strip()
                    message_body = parts[2].strip()
                    metadata = yaml.safe_load(yaml_content)
                    metadata['body'] = message_body
                    return metadata
            
            # Fallback: treat as plain message
            return {
                'id': datetime.now(timezone.utc).isoformat(),
                'from': 'cc',
                'for': 'jules',
                'action': 'message',
                'payload': {'content': content}
            }
            
        except Exception as e:
            self.log_error(f"Failed to read message: {e}")
            return None
    
    def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process handoff message and generate response"""
        action = message.get('action', 'unknown')
        payload = message.get('payload', {})
        
        response = {
            'id': datetime.now(timezone.utc).isoformat(),
            'from': 'jules',
            'for': message.get('from', 'cc'),
            'action': f"{action}_response",
            'payload': {}
        }
        
        try:
            if action == 'add_file':
                result = self.handle_add_file(payload)
            elif action == 'run_task':
                result = self.handle_run_task(payload)
            elif action == 'message':
                result = self.handle_message(payload)
            else:
                result = {'status': 'error', 'message': f"Unknown action: {action}"}
            
            response['payload'] = result
            
        except Exception as e:
            response['payload'] = {
                'status': 'error',
                'message': f"Error processing {action}: {str(e)}"
            }
        
        return response
    
    def handle_add_file(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle file creation requests"""
        file_path = payload.get('path')
        contents = payload.get('contents')
        
        if not file_path or contents is None:
            return {'status': 'error', 'message': 'Missing path or contents'}
        
        target_path = self.workspace / file_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(target_path, 'w') as f:
            f.write(contents)
        
        return {
            'status': 'success',
            'message': f"File created: {file_path}",
            'path': str(target_path)
        }
    
    def handle_run_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle task execution requests"""
        task = payload.get('task', 'No task specified')
        
        # For now, just acknowledge the task
        return {
            'status': 'acknowledged',
            'message': f"Task received: {task}",
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def handle_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle general message requests"""
        content = payload.get('content', 'Empty message')
        
        return {
            'status': 'received',
            'message': f"Message acknowledged: {len(content)} characters",
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def write_response(self, response: Dict[str, Any]) -> None:
        """Write response to output file"""
        try:
            # Format as YAML frontmatter + markdown
            yaml_data = {k: v for k, v in response.items() if k != 'body'}
            body = response.get('body', f"Response to {response.get('action', 'unknown')}")
            
            content = "---\n"
            content += yaml.dump(yaml_data, default_flow_style=False)
            content += "---\n\n"
            content += body
            
            with open(self.output_file, 'w') as f:
                f.write(content)
                
        except Exception as e:
            self.log_error(f"Failed to write response: {e}")
    
    def log_error(self, message: str) -> None:
        """Log error message"""
        timestamp = datetime.now(timezone.utc).isoformat()
        print(f"[{timestamp}] ERROR: {message}", file=sys.stderr)
    
    def log_info(self, message: str) -> None:
        """Log info message"""
        timestamp = datetime.now(timezone.utc).isoformat()
        print(f"[{timestamp}] INFO: {message}")
    
    def poll_once(self) -> bool:
        """Run one polling cycle, return True if message was processed"""
        message = self.read_message()
        if not message:
            return False
        
        self.log_info(f"Processing message: {message.get('action', 'unknown')}")
        response = self.process_message(message)
        self.write_response(response)
        
        # Archive the processed message
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        archive_path = self.shared_dir / f"processed-{timestamp}.md"
        if self.input_file.exists():
            self.input_file.rename(archive_path)
        
        self.log_info(f"Response written, message archived to {archive_path.name}")
        return True
    
    def run_poller(self, interval: int = 10) -> None:
        """Run continuous polling loop"""
        self.log_info(f"Starting handoff poller (interval: {interval}s)")
        
        try:
            while True:
                self.poll_once()
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.log_info("Poller stopped by user")
        except Exception as e:
            self.log_error(f"Poller crashed: {e}")
            raise

def main():
    workspace = os.environ.get('ASSISTANT_PROJECT_ROOT', '/mnt/c/Users/david/jules-workspace')
    
    if not os.path.exists(workspace):
        print(f"ERROR: Workspace not found: {workspace}", file=sys.stderr)
        sys.exit(1)
    
    poller = HandoffPoller(workspace)
    
    if '--check-once' in sys.argv:
        processed = poller.poll_once()
        if processed:
            print("Message processed successfully")
        else:
            print("No messages to process")
    else:
        poller.run_poller()

if __name__ == '__main__':
    main()