import asyncio
import logging
import json

from aiogram.utils import executor
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery

from Controller import go_back, update_data, get_data, read_config, save_conversation
from keyboards.inline import create_keyboard, callback
from handlers import Math, Physics, Philology, General, Geography, Text
from misc import Form


logging.basicConfig(level=logging.INFO)

bot = Bot(read_config()["TOKEN"])
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.message_handlers.once = False


class VirtualBotAssistant:

    def __init__(self):
        self.bot = bot
        self.topics = {
            "Математика": ['Знайти площу прямокутника', 'Знайти площу кола', 'Знайти н-те число Фібоначчі',
                           'Знайти sin(x) та cos(x).', 'Знайти координати точки перетину двох прямих, заданих векторами'
                           ],
            "Фізика": ['Силу за законом всесвітнього тяжіння Ньютона', 'Енергію за рівнянням Ейнштейна для мас-енергії',
                       'Рівняння Гейзенберга невизначенності', 'Індукцію магнітного поля за формулою Ампера'],
            "Філологія": ['Яка різниця між Present Simple та Present Continuous?', 'Яка різниця між Some та Any?',
                          'Яка різниця між іменником та прикметником?', 'Які роди іменників існують в українській мові?',
                          'Як утворити форму множини іменників в українській мові?'],
            "Географія": ['Назвіть 5 найвищих гір в світі та вкажіть їхні висоти.'],
            "Робота з текстом": ['Знайти десять найдовших слів і у тексті.',
                                 'Знайти найдовші слова, які починаються з голосної літери.',
                                 'Знайти найбільш часто вживану літеру в тексті.',
                                 'Знайти найдовші слова, які не містять голосних літер.'],
            "Загальні питання": ['Який зараз рік?', 'Скільки днів до Нового Року?', 'Який зараз місяць?',
                                 'Яка найбільша планета у Сонячній системі?', "Хто написав повість 'Кайдашева сім'я?",
                                 'Яка найвища гора у світі?', 'Яка найбільша ріка у світі?',
                                 'Як називається процес перетворення рідини в газ?', 'Яка столиця Японії?',
                                 'Яка країна має найбільшу кількість населення?',
                                 'Які три кольори є основними у візуальному спектрі?']
        }
        self.topic_to_handler = {
            "Математика": Math,
            "Фізика": Physics,
            "Філологія": Philology,
            "Географія": Geography,
            "Робота з текстом": Text,
            "Загальні питання": General
        }
        self.topic_to_state = {
            "Математика": Form.math,
            "Фізика": Form.physics,
            "Філологія": Form.philology,
            "Географія": Form.geography,
            "Робота з текстом": Form.text,
            "Загальні питання": Form.general
        }
        self.state = Form.menu
        self.handler = None
        self.current_state = None
        self.keyboard = None

        @dp.message_handler(commands=['start', 'help'])
        async def cmd_start(message: types.Message, state: FSMContext):
            self.message = f'Вітаю, мене звати {VirtualBotAssistant.__name__}. Ви можете задати мені питання з ' \
                           f'наступних тем:\n{", ".join(str(x) for x in self.topics)}'
            self.keyboard = create_keyboard(self.topics.keys(), False)
            await message.answer(self.message, reply_markup=self.keyboard)
            await save_conversation(message=message, text=self.message)
            await Form.menu.set()
            await state.update_data(state_stack=[Form.menu], message_stack=[self.message], keyboard_stack=[self.keyboard])

        @dp.message_handler(state=Form.menu)
        async def menu_handler(message: types.Message, state: FSMContext):
            if message.text in ['Назад', 'Допомога', 'Завершити діалог']:
                return
            if message.text in self.topics:
                self.handler = None
                menu_answer = f'Ви обрали тему «{message.text}». Ви можете задати  мені питання з наступних тем:\n' \
                              f'{", ".join(str(x) for x in self.topics[f"{message.text}"])}'
                handler = self.topic_to_handler.get(message.text)
                self.handler = handler(dp, self.topics[message.text])
                await message.answer(menu_answer, reply_markup=self.handler.keyboard)
                await save_conversation(message=message, text=menu_answer)
                self.current_state = self.topic_to_state.get(message.text)
                await self.current_state.set()
                await update_data(state, self.current_state, menu_answer, self.handler.keyboard)
            else:
                unsuccessful_answer = f"Я не знаю цієї теми, натомість, ви можете задати мені питання з наступних тем"
                await message.answer(unsuccessful_answer, reply_markup=self.keyboard)
                await save_conversation(message=message, text=unsuccessful_answer)

        @staticmethod
        @dp.message_handler(text="Назад", state='*')
        async def return_handler(message: types.Message, state: FSMContext):
            current_state = await state.get_state()
            if current_state != Form.menu.state:
                prev_state, prev_message, prev_keyboard = await go_back(state)
                await message.answer(prev_message, reply_markup=prev_keyboard)
                await save_conversation(message=message, text=prev_message)
                await prev_state.set()
            else:
                await message.answer(self.message, reply_markup=self.keyboard)
                await save_conversation(message=message, text=self.message)

        @staticmethod
        @dp.message_handler(text="Завершити діалог", state='*')
        async def finish_handler(message: types.Message, state: FSMContext):
            current_state = await state.get_state()
            if current_state is None:
                return
            await state.finish()
            finish_message = 'Радий був поспілкуватись, до зустрічі.'
            await message.answer(finish_message, reply_markup=types.ReplyKeyboardRemove())
            await save_conversation(message=message, text=finish_message)

    @staticmethod
    @dp.message_handler(state='*')
    async def save_user_message(message: types.Message):
        await save_conversation(message=message, is_bot=False)

    @staticmethod
    @dp.message_handler(text=["Допомога", "help"], state='*')
    async def help_handler(message: types.Message, state: FSMContext):
        state, help_message, help_keyboard = await get_data(state)
        help_answer = help_message + 'Для завершення діалогу, натисніть «Завершити діалог». Для повернення до ' \
                                     'попереднього етапу, натисніть «Назад».'
        await message.answer(help_answer, reply_markup=help_keyboard)


if __name__ == '__main__':
    assistant = VirtualBotAssistant()
    loop = asyncio.get_event_loop()
    executor.start_polling(dp)
