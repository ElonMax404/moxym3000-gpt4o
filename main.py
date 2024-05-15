import openai
import pyautogui
from PIL import Image
from typing_extensions import Self
import base64
from io import BytesIO  

client = openai.OpenAI()

class StreamWrapper:
    def __init__(self, stream: openai.Stream) -> Self:
        self.stream = stream
        self.message = ""
    def get(self, display: bool = False) -> str:
        if display:
            print("Moxym-3000: ", end="")
        for chunk in self.stream:
            if chunk.choices[0].delta.content is not None:
                new_tokens = chunk.choices[0].delta.content
                self.message += new_tokens
                if display:
                    print(new_tokens, end="")
        if display:
            print()
        return self.message


class Agent:
    def __init__(self) -> Self:
        instructions: str = open("instructions.txt").read()
        self.messages = [{"role": "system", "content": instructions}]
        self.model: str = "gpt-4o"
        self.mouse_position = pyautogui.Point
        self.actions_buffer = ['None']

    def encode_image(image: Image):
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue())
        return img_str.decode('utf-8')

    def screenshot(self) -> Image:
        return pyautogui.screenshot()
    def prompt(self, text: str) -> StreamWrapper:

        self.mouse_position = pyautogui.position()
        base64_image = Agent.encode_image(self.screenshot())
        self.messages.append(
                {
                    "role": "user", 
                    "content": [{"type": "text", "text": f"{text}. [INFO: MOUSE_POSITION = ({self.mouse_position.x}, {self.mouse_position.y})]"},
                                 {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }]
                }
            )
        stream = client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            stream=True,
        )
        return StreamWrapper(stream)
    def parse_output(self, output: str):
        self.messages.append(
            {
                "role": "assistant",
                "content": output
            }
        )
        
        commands_string = output.split("{{")[1].split("}}")[0]
        commands = commands_string.split("&&")
        for command in commands:
            command = command.strip()
            self.actions_buffer.append(command)
            
        
    
    def perform(self):
        for action in self.actions_buffer:
            print(f"Performing action: {action}")
            if action.startswith("!move_mouse_by"):
                action = action.split("(")[1]
                x, y = action.split(",")
                y = y.split(")")[0]
                pyautogui.moveRel(int(x), int(y))
            elif action == "!RMB_click":
                pyautogui.rightClick()
            elif action == "!LMB_click":
                pyautogui.leftClick()
            elif action.startswith("!keyboard_input"):
                text = action.split("(")[1].split(")")[0]
                pyautogui.write(text)
            elif action.startswith("!sleep"):
                seconds = float(action.split("(")[1].split(")")[0])
                pyautogui.sleep(seconds)
            elif action == "None":
                pass
            else:
                raise ValueError(f"Unimplemented action requested by model: {action}")
        self.actions_buffer.clear()
                

def main():
    agent1 = Agent()
    running = True
    while running:
        user = input("Enter prompt: ")
        pyautogui.sleep(1)
        output = agent1.prompt(user).get(display=True)
        agent1.parse_output(output)
        agent1.perform()
        second_pass = agent1.prompt("Look at the screen. Did that bring expected results? If not, adjust accordingly and try again.").get(display=True)
        agent1.parse_output(second_pass)
        agent1.perform()



main()

