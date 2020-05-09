from typing import List, Optional

import pydantic


class Translation(pydantic.BaseModel):
    text: str
    note: Optional[str]


class Meanings(pydantic.BaseModel):
    sound_url: Optional[str] = pydantic.Field(..., alias='soundUrl')
    image_url: Optional[str] = pydantic.Field(..., alias='imageUrl')
    preview_url: Optional[str] = pydantic.Field(..., alias='previewUrl')
    translation: Translation


class Word(pydantic.BaseModel):
    text: str
    meanings: List[Meanings]

    def get_sound_url(self) -> Optional[str]:
        for meaning in self.meanings:
            if meaning.sound_url is not None:
                return f'https:{meaning.sound_url}'

    def get_image_url(self) -> Optional[str]:
        for meaning in self.meanings:
            if meaning.preview_url is not None:
                return f'https:{meaning.image_url}'


class WordList(pydantic.BaseModel):
    __root__: List[Word]

    def get_first_word_with_sound(self) -> Optional[Word]:
        for word in self.__root__:
            if word.get_sound_url():
                return word
        return None
