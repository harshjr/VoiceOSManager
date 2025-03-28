# VoiceOS Manager

## Overview

VoiceOS Manager is a voice-controlled system management tool that allows users to interact with their operating system using voice commands. Built with Python, it leverages speech recognition to start, kill, and prioritize processes, monitor system metrics (CPU, memory, and process details), and display real-time updates through a Tkinter-based GUI. The project includes a security module to ensure safe operation, especially when handling sensitive applications.

This project was developed as part of an academic assignment to demonstrate the integration of voice recognition, system monitoring, and GUI development in a secure and user-friendly application.

## Features

- **Voice Command Processing**: Start, kill, and prioritize processes using voice commands (e.g., "start notepad", "kill chrome", "prioritize high").
- **System Monitoring**: Real-time monitoring of CPU usage, memory usage, and running processes using the `psutil` library.
- **Graphical User Interface**: Displays process lists and resource usage graphs (CPU and memory) using Tkinter and Matplotlib.
- **Security Module**:
  - User authentication with a login system to restrict access.
  - Authorization prompts for launching sensitive applications (e.g., Terminal, Command Prompt).
  - Command logging for auditing and tracking actions.
  - Offline speech recognition using `PocketSphinx` to enhance privacy (replaced Google Speech Recognition API).
  - Least privilege execution to minimize security risks.
- **Cross-Platform Support**: Compatible with Windows, macOS, and Linux (with some OS-specific commands).

## System Architecture

The VoiceOS Manager follows a modular architecture, as shown in the diagram below:

![Overall System Architecture](diagrams/overall_system_architecture.png)

### Components:
- **User**: Interacts with the system by speaking commands.
- **Microphone**: Captures the user's voice input.
- **Speech Recognition Module**: Converts audio into text commands using `PocketSphinx`.
- **Command Processor**: Parses text commands and maps them to actions.
- **System Monitoring Module**: Fetches system metrics (CPU, memory, processes) using `psutil`.
- **Process Manager**: Executes actions like starting, killing, or prioritizing processes.
- **Tkinter GUI**: Displays process lists, resource graphs, and feedback to the user.
- **Operating System**: Interacts with the system to execute commands and fetch data.

### Data Flow:
- User → Microphone ("Voice Input").
- Microphone → Speech Recognition Module ("Audio Data").
- Speech Recognition Module → Command Processor ("Text Command").
- Command Processor → Process Manager ("Action Command").
- Command Processor → Tkinter GUI ("Feedback", dashed).
- System Monitoring Module → Tkinter GUI ("System Metrics").
- System Monitoring Module ↔ Operating System ("Fetch Metrics", bidirectional).
- Process Manager ↔ Operating System ("Execute Actions", bidirectional).
- Tkinter GUI → User ("Visual Feedback", dashed).

## System Monitoring Data Flow

The system monitoring process updates the GUI every 5 seconds, as shown in the diagram below:

![System Monitoring Data Flow](diagrams/system_monitoring_data_flow.png)

### Components:
- **Operating System**: Provides system data.
- **Fetch Metrics**: Fetches data using `psutil`.
- **System Metrics**: Represents CPU and memory usage data.
- **Process List Data**: Represents the list of running processes.
- **Update Process List**: Updates the Tkinter Treeview widget with process details.
- **Update Resource Graph**: Updates the Matplotlib bar chart with CPU/memory usage.
- **Tkinter GUI**: Displays the updated process list and resource graph.

### Data Flow:
- Operating System → Fetch Metrics ("System Data").
- Fetch Metrics → System Metrics ("CPU/Memory Usage").
- Fetch Metrics → Process List Data ("Process Details").
- System Metrics → Update Resource Graph ("Graph Data").
- Process List Data → Update Process List ("Process Data").
- Update Process List → Tkinter GUI ("Display Processes").
- Update Resource Graph → Tkinter GUI ("Display Graph").
- Tkinter GUI → Fetch Metrics ("Every 5 Seconds", dashed).

## Security Features

The VoiceOS Manager includes a security module to ensure safe operation:

- **User Authentication**: Requires login credentials to access the application.
- **Authorization for Sensitive Applications**: Prompts for secondary confirmation when launching sensitive applications (e.g., Terminal, Command Prompt).
- **Command Logging**: Logs all executed commands to a secure file (`voiceos_manager.log`) for auditing.
- **Offline Speech Recognition**: Uses `PocketSphinx` for offline speech recognition to prevent audio data from being sent over the internet.
- **Least Privilege Execution**: Runs with minimal privileges and prompts for elevation only when necessary.

### Security Check Process

The security check process ensures that only authorized users can execute commands, as shown in the diagram below:

![Security Check Process](diagrams/security_check_process.png)

- **Steps**:
  1. Start → User Login.
  2. User Login → Credentials Valid? (decision).
  3. Credentials Valid? → Enable Voice Commands (if Yes).
  4. Credentials Valid? → End (if No, show error).
  5. Enable Voice Commands → Sensitive Command? (decision).
  6. Sensitive Command? → Prompt for Authorization (if Yes).
  7. Sensitive Command? → Execute Command (if No).
  8. Prompt for Authorization → Authorization Granted? (decision).
  9. Authorization Granted? → Execute Command (if Yes).
  10. Authorization Granted? → End (if No, cancel action).
  11. Execute Command → Log Command → End.

## Installation

### Prerequisites
- Python 3.8 or higher
- A microphone for voice input
- Operating System: Windows, macOS, or Linux

### Dependencies
Install the required Python libraries using `pip`:

```bash
pip install speechrecognition pocketsphinx psutil matplotlib tkinter
