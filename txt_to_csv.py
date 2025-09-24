import csv
import re
from datetime import datetime

def parse_messages_to_csv(input_text, output_file='messages.csv'):
    """
    Parse message format and convert to CSV with dates, messages, and sender names.
    """
    lines = input_text.strip().split('\n')
    messages = []
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines
        if not line:
            i += 1
            continue
            
        # Skip tapbacks and attachments
        if line.startswith('Tapbacks:') or line.startswith('/Users/') or line.startswith('Loved by') or line.startswith('(Read by'):
            i += 1
            continue
            
        # Check if line starts with a date pattern
        date_pattern = r'^[A-Za-z]{3}\s+\d{1,2},\s+\d{4}'
        if re.match(date_pattern, line):
            # Extract date and time
            date_time_match = re.match(r'^([A-Za-z]{3}\s+\d{1,2},\s+\d{4}\s+\d{1,2}:\d{2}:\d{2}\s+[AP]M)', line)
            if date_time_match:
                date_time = date_time_match.group(1)
                
                # Look for sender on next line or same line after timestamp info
                i += 1
                if i < len(lines):
                    next_line = lines[i].strip()
                    
                    # Check if next line is a phone number (Catherine) or Ryan
                    if next_line.startswith('+13055091214'):
                        sender = 'Catherine'
                        i += 1  # Move to message line
                        if i < len(lines):
                            message = lines[i].strip()
                            messages.append([date_time, sender, message])
                    elif next_line == 'Ryan':
                        sender = 'Ryan'
                        i += 1  # Move to message line
                        if i < len(lines):
                            message = lines[i].strip()
                            messages.append([date_time, sender, message])
                    else:
                        # Message might be on the same line after timestamp
                        remaining_text = line[date_time_match.end():].strip()
                        if remaining_text:
                            # Need to determine sender from context or previous patterns
                            i += 1
                            continue
        else:
            i += 1
    
    # Write to CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Date', 'Sender', 'Message'])  # Header
        writer.writerows(messages)
    
    print(f"Converted {len(messages)} messages to {output_file}")
    return messages

# Enhanced version that handles the format more accurately
def parse_messages_to_csv_enhanced(input_text, output_file='messages.csv'):
    """
    Enhanced parser that better handles the message format.
    """
    lines = input_text.strip().split('\n')
    messages = []
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines, tapbacks, attachments, and read receipts
        if (not line or 
            line.startswith('Tapbacks:') or 
            line.startswith('/Users/') or 
            line.startswith('Loved by') or 
            line.startswith('(Read by')):
            i += 1
            continue
        
        # Look for date pattern at start of line
        date_match = re.match(r'^([A-Za-z]{3}\s+\d{1,2},\s+\d{4}\s+\d{1,2}:\d{2}:\d{2}\s+[AP]M)', line)
        if date_match:
            date_time = date_match.group(1)
            
            # Check what comes after the date on same line
            remaining = line[date_match.end():].strip()
            
            i += 1
            if i < len(lines):
                next_line = lines[i].strip()
                
                # Determine sender and message
                if next_line.startswith('+13055091214'):
                    sender = 'Catherine'
                    # Get the actual message
                    i += 1
                    if i < len(lines):
                        message = lines[i].strip()
                        # Skip if it's another control line
                        if not (message.startswith('Tapbacks:') or 
                               message.startswith('/Users/') or 
                               message.startswith('Loved by') or 
                               message.startswith('(Read by')):
                            messages.append([date_time, sender, message])
                elif next_line == 'Ryan':
                    sender = 'Ryan'
                    # Get the actual message
                    i += 1
                    if i < len(lines):
                        message = lines[i].strip()
                        # Skip if it's another control line
                        if not (message.startswith('Tapbacks:') or 
                               message.startswith('/Users/') or 
                               message.startswith('Loved by') or 
                               message.startswith('(Read by')):
                            messages.append([date_time, sender, message])
                else:
                    # Handle case where sender might be implied or message is direct
                    continue
        else:
            i += 1
    
    # Write to CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Date', 'Sender', 'Message'])
        writer.writerows(messages)
    
    print(f"Converted {len(messages)} messages to {output_file}")
    return messages

def parse_file_to_csv(input_file, output_file='parsed_messages.csv'):
    """
    Read messages from a text file and convert to CSV.
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            input_text = file.read()
        
        messages = parse_messages_to_csv_enhanced(input_text, output_file)
        return messages
        
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
        return []
    except Exception as e:
        print(f"Error reading file: {e}")
        return []

# Example usage:
if __name__ == "__main__":
    # Replace 'messages.txt' with your actual file name
    input_filename = 'conversation.txt'
    output_filename = 'parsed_messages.csv'
    
    messages = parse_file_to_csv(input_filename, output_filename)
    
    if messages:
        print(f"Successfully parsed {len(messages)} messages!")
        print("First few messages:")
        for i, (date, sender, message) in enumerate(messages[:3]):
            print(f"{i+1}. {date} - {sender}: {message}")
    else:
        print("No messages were parsed.")