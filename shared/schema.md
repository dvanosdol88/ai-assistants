# Handoff Message Schema
#
# id: RFC-3339 timestamp, unique per message
# from: assistant name ("cc", "jules", "ccp", etc.)
# for:  target assistant
# action: verb ("add_file", "run_task", ...)
# payload: arbitrary JSON/YAML block with action args
#
# Example:
# id: 2025-07-01T14:32:10Z
# from: cc
# for:  jules
# action: add_file
# payload:
#   path: LICENSE
#   contents:  < /dev/null | 
#     MIT License…
