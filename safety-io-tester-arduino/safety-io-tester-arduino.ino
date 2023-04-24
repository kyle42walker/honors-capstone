/*
 * File:   safety-io-tester-arduino.ino
 * Author: Kyle Walker (UMass Lowell Honors Capstone Project)
 *         Richard Barrett (Brooks SQA)
 * Date:   2023-04-24
 *
 * This program is designed to run on an Arduino Mega 2560 on the safety
 * I/O test board. It reads and writes safety I/O signals of the robot and
 * sends the results over RS232 to a monitoring computer.
 */

// Constants
const int BLINK_INTERVAL = 500; // Milliseconds between LED blinks

// Arduino output pin definitions (robot inputs)
const int E_STOP_A_COMMAND = 25;    // Safety pin 21 (relay 3) *
const int E_STOP_B_COMMAND = 34;    // Safety pin 24 (relay 2) *
const int INTERLOCK_A_COMMAND = 23; // Safety pin 22 (relay 4) *
const int INTERLOCK_B_COMMAND = 32; // Safety pin 23 (relay 1) *
const int MODE_1_A_COMMAND = 29;    // Safety pin 19 *
const int MODE_1_B_COMMAND = 38;    // Safety pin 26 *
const int MODE_2_A_COMMAND = 27;    // Safety pin 20 *
const int MODE_2_B_COMMAND = 36;    // Safety pin 25 *

// Arduino output pin definitions (test board inputs)
const int POWER_COMMAND = 49;     // Power Relay Control (relay 5) *
const int H_BEAT_TEST_BOARD = 51; // Heart beat LED on test board *

// Arduino input pin defintions (robot outputs)
const int POWER_24V_A_RESPONSE = 53;  // Safety pin 12 *
const int POWER_24V_B_RESPONSE = 40;  // Safety pin 16 *
const int E_STOP_A_RESPONSE = 33;     // Safety pin 01 *
const int E_STOP_B_RESPONSE = 46;     // Safety pin 09 *
const int STOP_A_RESPONSE = 37;       // Safety pin 02 *
const int STOP_B_RESPONSE = 48;       // Safety pin 08 *
const int INTERLOCK_A_RESPONSE = 41;  // Safety pin 04 *
const int INTERLOCK_B_RESPONSE = 52;  // Safety pin 06 *
const int MODE_1_A_RESPONSE = 31;     // Safety pin 10 *
const int MODE_1_B_RESPONSE = 42;     // Safety pin 18 *
const int MODE_2_A_RESPONSE = 35;     // Safety pin 11 *
const int MODE_2_B_RESPONSE = 50;     // Safety pin 17 *
const int TEACH_MODE_A_RESPONSE = 39; // Safety pin 13 *
const int TEACH_MODE_B_RESPONSE = 47; // Safety pin 15 *
const int HEARTBEAT_A_RESPONSE = 45;  // Safety pin 05 *
const int HEARTBEAT_B_RESPONSE = 43;  // Safety pin 14 *

// Global variables for handling e-stop and interlock delays
unsigned long eStopDelay_ms = 0;           // Delay (ms) to trigger second e-stop pin
char eStopChannel = 'A';                   // Which channel to trigger e-stop on
uint8_t eStopState = LOW;                  // State to set e-stop output pin to
unsigned long eStopTriggerTime_ms = 0;     // Time first e-stop pin was triggered
unsigned long interlockDelay_ms = 0;       // Delay (ms) to trigger second interlock pin
char interlockChannel = 'A';               // Which channel to trigger interlock on
uint8_t interlockState = LOW;              // State to set interlock output pin to
unsigned long interlockTriggerTime_ms = 0; // Time first interlock pin was triggered

void setup()
{
    // Start debug port at 9600 baud
    Serial.begin(9600);
    while (!Serial)
        ; // Wait for serial port to connect. Needed for native USB port only
    Serial.println("Debug port open");

    // Start control serial port at 115200 baud
    Serial1.setTimeout(10000);
    Serial1.begin(115200);
    Serial.println("Command port open");

    // Start lcd serial port at 9600 baud
    // Serial2.setTimeout(10000);
    // Serial2.begin(9600);
    // Serial.println("LCD port open");

    // Output pins
    pinMode(LED_BUILTIN, OUTPUT);
    pinMode(E_STOP_A_COMMAND, OUTPUT);
    pinMode(E_STOP_B_COMMAND, OUTPUT);
    pinMode(INTERLOCK_A_COMMAND, OUTPUT);
    pinMode(INTERLOCK_B_COMMAND, OUTPUT);
    pinMode(MODE_1_A_COMMAND, OUTPUT);
    pinMode(MODE_1_B_COMMAND, OUTPUT);
    pinMode(MODE_2_A_COMMAND, OUTPUT);
    pinMode(MODE_2_B_COMMAND, OUTPUT);
    pinMode(POWER_COMMAND, OUTPUT);
    pinMode(H_BEAT_TEST_BOARD, OUTPUT);

    // Input pins
    pinMode(POWER_24V_A_RESPONSE, INPUT_PULLUP);
    pinMode(POWER_24V_B_RESPONSE, INPUT_PULLUP);
    pinMode(E_STOP_A_RESPONSE, INPUT_PULLUP);
    pinMode(E_STOP_B_RESPONSE, INPUT_PULLUP);
    pinMode(STOP_A_RESPONSE, INPUT_PULLUP);
    pinMode(STOP_B_RESPONSE, INPUT_PULLUP);
    pinMode(INTERLOCK_A_RESPONSE, INPUT_PULLUP);
    pinMode(INTERLOCK_B_RESPONSE, INPUT_PULLUP);
    pinMode(MODE_1_A_RESPONSE, INPUT_PULLUP);
    pinMode(MODE_1_B_RESPONSE, INPUT_PULLUP);
    pinMode(MODE_2_A_RESPONSE, INPUT_PULLUP);
    pinMode(MODE_2_B_RESPONSE, INPUT_PULLUP);
    pinMode(TEACH_MODE_A_RESPONSE, INPUT_PULLUP);
    pinMode(TEACH_MODE_B_RESPONSE, INPUT_PULLUP);
    pinMode(HEARTBEAT_A_RESPONSE, INPUT_PULLUP);
    pinMode(HEARTBEAT_B_RESPONSE, INPUT_PULLUP);

    // Initialize output pins to look like muting connector
    digitalWrite(E_STOP_A_COMMAND, LOW);
    digitalWrite(E_STOP_B_COMMAND, LOW);
    digitalWrite(INTERLOCK_A_COMMAND, LOW);
    digitalWrite(INTERLOCK_B_COMMAND, LOW);
    digitalWrite(MODE_1_A_COMMAND, LOW);
    digitalWrite(MODE_1_B_COMMAND, LOW);
    digitalWrite(MODE_2_A_COMMAND, HIGH);
    digitalWrite(MODE_2_B_COMMAND, HIGH);
    digitalWrite(POWER_COMMAND, LOW);

    // Initialize LED pins to off
    digitalWrite(LED_BUILTIN, LOW);
    digitalWrite(H_BEAT_TEST_BOARD, LOW);

    Serial.println("Initialized");
} // End setup()

void loop()
{
    // Check "timers" and update outputs
    unsigned long currentMillis = millis(); // Current time
    blinkLeds(currentMillis);
    handleEStopDelay(currentMillis);
    handleInterlockDelay(currentMillis);

    // If there is data in the serial buffer, read it and parse it
    if (Serial1.available() <= 0)
        return;

    String cmd = Serial1.readStringUntil('\n');

    // Echo command
    Serial.print("cmd: ");
    Serial.println(cmd);

    // Parse command and generate response
    String response = "";
    switch (cmd[0])
    {
    case 'R': // Read requested
        response = processReadRequest(cmd);
        break;
    case 'M': // Set mode
        response = processSetMode(cmd);
        break;
    case 'E': // Set e-stop
        response = processSetEStop(cmd);
        break;
    case 'I': // Set interlock
        response = processSetInterlock(cmd);
        break;
    case 'P': // Set power
        response = processSetPower(cmd);
        break;
    case 'H': // Heartbeat requested
        response = processHeartbeatRequest(cmd);
        break;
    case 'S': // Set echo string
        response = processSetEchoString(cmd);
        break;
    case 'A': // Set all robot inputs
        response = processSetAll(cmd);
        break;
    default: // Else not a valid command
        response = "ERR\n";
        break;
    }

    //  If there is a response, send it to the host
    if (response.length() <= 0)
        return;

    Serial.print("resp: ");
    Serial.println(response);

    // Respond to host
    Serial1.println(response);
} // End loop()

void blinkLeds(int currentMillis)
{
    // LED heartbeat function
    static unsigned long previousMillis = 0; // Last time the LED was updated
    if (currentMillis - previousMillis >= BLINK_INTERVAL)
    {
        // Store the last time the LED was updated
        previousMillis = currentMillis;

        // Toggle LEDs
        digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
        digitalWrite(H_BEAT_TEST_BOARD, !digitalRead(H_BEAT_TEST_BOARD));
    }
} // End blinkLeds()

void handleEStopDelay(int currentMillis)
{
    // E-Stop delay function
    if (eStopDelay_ms <= 0)
        return;

    if (currentMillis - eStopTriggerTime_ms >= eStopDelay_ms)
    {
        // Reset delay
        eStopDelay_ms = 0;

        // Set E-Stop
        if (eStopChannel == 'A')
            digitalWrite(E_STOP_A_COMMAND, eStopState);
        else if (eStopChannel == 'B')
            digitalWrite(E_STOP_B_COMMAND, eStopState);
    }
} // End handleEStopDelay()

void handleInterlockDelay(int currentMillis)
{
    // Interlock delay function
    if (interlockDelay_ms <= 0)
        return;

    if (currentMillis - interlockTriggerTime_ms >= interlockDelay_ms)
    {
        // Reset delay
        interlockDelay_ms = 0;

        // Set Interlock
        if (interlockChannel == 'A')
            digitalWrite(INTERLOCK_A_COMMAND, interlockState);
        else if (interlockChannel == 'B')
            digitalWrite(INTERLOCK_B_COMMAND, interlockState);
    }
} // End handleInterlockDelay()

String processReadRequest(String cmd)
{
    /*
    Response should be in the following format:
        Index   Data byte
            0   A
            1   (0|1) - Mode A1
            2   (0|1) - Mode A2
            3   (0|1) - E-Stop A
            4   (0|1) - Interlock A
            5   (0|1) - Stop A
            6   (0|1) - Teach Mode A
            7   (0|1) - Heartbeat A
            8   (0|1) - Power A
            9   B
            10  (0|1) - Mode B1
            11  (0|1) - Mode B2
            12  (0|1) - E-Stop B
            13  (0|1) - Interlock B
            14  (0|1) - Stop B
            15  (0|1) - Teach Mode B
            16  (0|1) - Heartbeat B
            17  (0|1) - Power B
            18  \n

    e.g. "R\n" requests the output pin states and a response of "A10000010B01000010\n"
    indicates Mode A1, Heartbeat A, Mode B2, and Heartbeat B are set
    and all other pins are cleared
    */
    String response = "";

    // Check if command is valid
    if (cmd.length() != 1)
        return response;

    // Read state from robot
    response += "A";
    response += String(digitalRead(MODE_1_A_RESPONSE));
    response += String(digitalRead(MODE_2_A_RESPONSE));
    response += String(digitalRead(E_STOP_A_RESPONSE));
    response += String(digitalRead(INTERLOCK_A_RESPONSE));
    response += String(digitalRead(STOP_A_RESPONSE));
    response += String(digitalRead(TEACH_MODE_A_RESPONSE));
    response += String(digitalRead(HEARTBEAT_A_RESPONSE));
    response += String(digitalRead(POWER_24V_A_RESPONSE));
    response += "B";
    response += String(digitalRead(MODE_1_B_RESPONSE));
    response += String(digitalRead(MODE_2_B_RESPONSE));
    response += String(digitalRead(E_STOP_B_RESPONSE));
    response += String(digitalRead(INTERLOCK_B_RESPONSE));
    response += String(digitalRead(STOP_B_RESPONSE));
    response += String(digitalRead(TEACH_MODE_B_RESPONSE));
    response += String(digitalRead(HEARTBEAT_B_RESPONSE));
    response += String(digitalRead(POWER_24V_B_RESPONSE));
    response += "\n";

    return response;
} // End processReadRequest()

String processSetMode(String cmd)
{
    /*
    Parse data in the following format:
        Index   Data byte
            0   M
            1   (0|1) - Mode A1
            2   (0|1) - Mode A2
            3   (0|1) - Mode B1
            4   (0|1) - Mode B2
            5   \n

    e.g. "M1001\n" sets bits A1 and B2, setting the controller to "Manual" mode
    */
    if (cmd.length() != 5)
        return "ERR\n";

    // Set mode pins
    digitalWrite(MODE_1_A_COMMAND, cmd[1] == '1' ? HIGH : LOW);
    digitalWrite(MODE_2_A_COMMAND, cmd[2] == '1' ? HIGH : LOW);
    digitalWrite(MODE_1_B_COMMAND, cmd[3] == '1' ? HIGH : LOW);
    digitalWrite(MODE_2_B_COMMAND, cmd[4] == '1' ? HIGH : LOW);

    // Success
    return "OK\n";
} // End processSetMode()

String processSetEStop(String cmd)
{
    /*
    Parse data in the following format:
        Index   Data byte
            0   E
            1   (0|1) - E-stop A
            2   (0|1) - E-stop B

            Optional 5-digit delay in milliseconds
            3   (A|B) - Which e-stop channel to set first before the delay
            4   (0-9)
            5   (0-9)
            6   (0-9)
            7   (0-9)
            8   (0-9)

            3 | 9   \n

    e.g. "E10" sets e-stop A ON and B OFF simultaneously,
    "E11B00100" sets e-stop A ON 100 ms after e-stop B ON
    */
    // No delay
    if (cmd.length() == 3)
    {
        // Set e-stop pins
        digitalWrite(E_STOP_A_COMMAND, cmd[1] == '1' ? HIGH : LOW);
        digitalWrite(E_STOP_B_COMMAND, cmd[2] == '1' ? HIGH : LOW);
    }

    // Delay
    else if (cmd.length() == 9)
    {
        // Parse delay
        eStopDelay_ms = cmd.substring(4, 9).toInt();

        // Set first e-stop pin
        if (cmd[3] == 'A')
        {
            digitalWrite(E_STOP_A_COMMAND, cmd[1] == '1' ? HIGH : LOW);
            eStopChannel = 'B';
            eStopState = cmd[2] == '1' ? HIGH : LOW;
        }
        else if (cmd[3] == 'B')
        {
            digitalWrite(E_STOP_B_COMMAND, cmd[2] == '1' ? HIGH : LOW);
            eStopChannel = 'A';
            eStopState = cmd[1] == '1' ? HIGH : LOW;
        }
        else
            return "ERR\n";
    }

    // Invalid command
    else
        return "ERR\n";

    // Success (respond after setting the first pin)
    return "OK\n";
} // End processSetEStop()

String processSetInterlock(String cmd)
{
    /*
    Parse data in the following format:
        Index   Data byte
            0   I
            1   (0|1) - Interlock A
            2   (0|1) - Interlock B

            Optional 5-digit delay in milliseconds
            3   (A|B) - Which interlock channel to set first before the delay
            4   (0-9)
            5   (0-9)
            6   (0-9)
            7   (0-9)
            8   (0-9)

            3 | 9   \n

    e.g. "I10" sets interlock A ON and B OFF simultaneously,
    "I11B00100" sets interlock A 100 ms after interlock B
    */
    // No delay
    if (cmd.length() == 3)
    {
        // Set interlock pins
        digitalWrite(INTERLOCK_A_COMMAND, cmd[1] == '1' ? HIGH : LOW);
        digitalWrite(INTERLOCK_B_COMMAND, cmd[2] == '1' ? HIGH : LOW);
    }

    // Delay
    else if (cmd.length() == 9)
    {
        // Parse delay
        interlockDelay_ms = cmd.substring(4, 9).toInt();

        // Set first interlock pin
        if (cmd[3] == 'A')
        {
            digitalWrite(INTERLOCK_A_COMMAND, cmd[1] == '1' ? HIGH : LOW);
            interlockChannel = 'B';
            interlockState = cmd[2] == '1' ? HIGH : LOW;
        }
        else if (cmd[3] == 'B')
        {
            digitalWrite(INTERLOCK_B_COMMAND, cmd[2] == '1' ? HIGH : LOW);
            interlockChannel = 'A';
            interlockState = cmd[1] == '1' ? HIGH : LOW;
        }
        else
            return "ERR\n";
    }

    // Invalid command
    else
        return "ERR\n";

    // Success (respond after setting the first pin)
    return "OK\n";
} // End processSetInterlock()

String processSetPower(String cmd)
{
    /*
    Parse data in the following format:
        Index   Data byte
            0   P
            1   (0|1) - Power
            2   \n

    e.g. "P1" sets power ON, "P0" sets power OFF
    */
    if (cmd.length() != 2)
        return "ERR\n";

    // Set power pin
    digitalWrite(POWER_COMMAND, cmd[1] == '1' ? HIGH : LOW);

    // Success
    return "OK\n";
} // End processSetPower()

String processHeartbeatRequest(String cmd)
{
    /*
    Response should be in the following format:
        Index   Data byte
            0   A
            1   (0-9)
            2   (0-9)
            3   (0-9)
            4   (0-9)
            5   (0-9)
            6   B
            7   (0-9)
            8   (0-9)
            9   (0-9)
            10  (0-9)
            11  (0-9)
            12  \n

    e.g. "H" requesets the heartbeat and a response of "A00100B01234" indicates
    the heartbeat on channel A is 100 Hz and the heartbeat on channel B is 1234 Hz
    */
    if (cmd.length() != 1)
        return "ERR\n";

    // Measure heartbeat
    // Compute the average of 3 pulseIn measurements on each channel
    unsigned long heartbeatPeriodA_us = 0;
    unsigned long heartbeatPeriodB_us = 0;
    for (int i = 0; i < 3; i++)
    {
        // Measure pulse width with 50 Hz (20000 us) timeout
        heartbeatPeriodA_us += pulseIn(HEARTBEAT_A_RESPONSE, HIGH, 20000);
        heartbeatPeriodA_us += pulseIn(HEARTBEAT_A_RESPONSE, LOW, 20000);
        heartbeatPeriodB_us += pulseIn(HEARTBEAT_B_RESPONSE, HIGH, 20000);
        heartbeatPeriodB_us += pulseIn(HEARTBEAT_B_RESPONSE, LOW, 20000);
    }
    heartbeatPeriodA_us /= 3;
    heartbeatPeriodB_us /= 3;

    // Convert to frequency in Hz (round down to nearest integer)
    int heartbeatFrequencyA_hz = 1000000 / heartbeatPeriodA_us;
    int heartbeatFrequencyB_hz = 1000000 / heartbeatPeriodB_us;

    // Convert frequency to string padded to 5 digits
    String heartbeatFrequencyA_str = String(heartbeatFrequencyA_hz);
    String heartbeatFrequencyB_str = String(heartbeatFrequencyB_hz);

    if (heartbeatFrequencyA_str.length() > 5 || heartbeatFrequencyB_str.length() > 5)
        return "ERR\n";

    while (heartbeatFrequencyA_str.length() < 5)
        heartbeatFrequencyA_str = "0" + heartbeatFrequencyA_str;

    while (heartbeatFrequencyB_str.length() < 5)
        heartbeatFrequencyB_str = "0" + heartbeatFrequencyB_str;

    // Send heartbeat response
    String response = "";
    response += "A";
    response += heartbeatFrequencyA_str;
    response += "B";
    response += heartbeatFrequencyB_str;
    response += "\n";

    return response;
} // End processHeartbeatRequest()

String processSetEchoString(String cmd)
{
    /*
    Send data to the serial device in the following format:
        Index   Data byte
            0   S
            1   Char 1
            2   Char 2
            ...
            N   Char N
            N+1 \n

        e.g. "SHello World!" sets the echo string to "Hello World!"
    */
    if (cmd.length() > 32)
        return "ERR\n";

    // Set echo string
    String echoString = cmd.substring(1, cmd.length());
    Serial.println(echoString);

    return "OK\n";
} // End processSetEchoString()

String processSetAll(String cmd)
{
    /*
    Parse data in the following format:
        Index   Data byte
            0   A
            1   (0|1) - Mode A1
            2   (0|1) - Mode A2
            3   (0|1) - E-stop A
            4   (0|1) - Interlock A
            5   B
            6   (0|1) - Mode B1
            7   (0|1) - Mode B2
            8   (0|1) - E-stop B
            9   (0|1) - Interlock B
            10  P
            11  (0|1) - Power
            12  \n

    e.g. "A1001B0111P1" sets mode A1 to ON, mode A2 to OFF, e-stop A to OFF,
    interlock A to ON, mode B1 to OFF, mode B2 to ON, e-stop B to ON,
    interlock B to ON, and power to ON
    */
    if (cmd.length() != 11)
        return "ERR\n";

    if (cmd[0] != 'A' || cmd[5] != 'B' || cmd[10] != 'P')
        return "ERR\n";

    // Set outputs
    digitalWrite(MODE_1_A_COMMAND, cmd[1] == '1' ? HIGH : LOW);
    digitalWrite(MODE_2_A_COMMAND, cmd[2] == '1' ? HIGH : LOW);
    digitalWrite(E_STOP_A_COMMAND, cmd[3] == '1' ? HIGH : LOW);
    digitalWrite(INTERLOCK_A_COMMAND, cmd[4] == '1' ? HIGH : LOW);
    digitalWrite(MODE_1_B_COMMAND, cmd[6] == '1' ? HIGH : LOW);
    digitalWrite(MODE_2_B_COMMAND, cmd[7] == '1' ? HIGH : LOW);
    digitalWrite(E_STOP_B_COMMAND, cmd[8] == '1' ? HIGH : LOW);
    digitalWrite(INTERLOCK_B_COMMAND, cmd[9] == '1' ? HIGH : LOW);
    digitalWrite(POWER_COMMAND, cmd[11] == '1' ? HIGH : LOW);

    // Success
    return "OK\n";
} // End processSetAll()
