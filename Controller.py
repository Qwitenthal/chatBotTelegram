import json
import time

from aiogram.dispatcher import FSMContext

def read_config():
    with open('config.json') as config_file:
        return json.load(config_file)


async def go_back(state: FSMContext):
    async with state.proxy() as data:
        prev_state, prev_message, prev_keyboard = data['state_stack'], data['message_stack'], data['keyboard_stack']
        await state.update_data(state_stack=prev_state.pop(),
                                message_stack=prev_message.pop(),
                                keyboard_stack=prev_keyboard.pop())
        cur_state, message, keyboard = prev_state[-1], prev_message[-1], prev_keyboard[-1]
        return cur_state, message, keyboard


async def update_data(state: FSMContext, current_state, message: str, keyboard):
     async with state.proxy() as data:
        prev_state, prev_message, prev_keyboard = data['state_stack'], data['message_stack'], data['keyboard_stack']
        if len(prev_state) > 5:
            prev_state = prev_state[1:]
            prev_message = prev_message[1:]
            prev_keyboard = prev_keyboard[1:]
        await state.update_data(state_stack=prev_state.append(current_state),
                                message_stack=prev_message.append(message),
                                keyboard_stack=prev_keyboard.append(keyboard))


async def get_data(state: FSMContext):
    async with state.proxy() as data:
        stack_state, stack_message, stack_keyboard = data['state_stack'], data['message_stack'], data['keyboard_stack']
        return stack_state[-1], stack_message[-1], stack_keyboard[-1]


async def save_conversation(message=None, text=None, is_bot=True):
    path = read_config()["PATH"] + '\\'
    full_path = f"{path}{message['chat'].username}.txt"
    text_to_save = f'BOT : {text}\n' if is_bot else f'USER : {text or message.text}\n'
    with open(full_path, 'a+', encoding="utf-8") as file:
        file.write(text_to_save)
