from pathlib import Path
from json import JSONEncoder, JSONDecoder
import random
from typing import Optional, List, Dict, Tuple
from httpx import AsyncClient
import ssl
import hashlib
from nonebot import require
require("nonebot_plugin_localstore")
import nonebot_plugin_localstore as store  # noqa: E402

class AlreadyExistsError(Exception):
    pass

async def init_quotation():
    for QUO_DIR in store.get_plugin_data_dir().iterdir():
        if not QUO_DIR.is_symlink():
            store.get_plugin_config_file(str(QUO_DIR.name + ".json")).write_text(
                JSONEncoder().encode( [key.name for key in QUO_DIR.iterdir()] ),
                encoding="u8",
            )


async def send_quo(args: str) -> Path:
    QUO_DIR = store.get_plugin_data_dir() / args
    ENSURE_THIS_PATH =  store.get_plugin_config_file(str(args + ".json")) if not QUO_DIR.is_symlink() else store.get_plugin_config_file(str(QUO_DIR.readlink().name + ".json"))
    ensure_pic_use: List[str] = JSONDecoder().decode(ENSURE_THIS_PATH.read_text(encoding="u8"))
    try:
        randompic = random.choice(ensure_pic_use)
    except IndexError:
        ensure_pic_use = [key.name for key in QUO_DIR.iterdir()]
        randompic = random.choice(ensure_pic_use)
    PIC_PATH : Path = QUO_DIR / randompic
    ensure_pic_use.remove(randompic)
    ENSURE_THIS_PATH.write_text(JSONEncoder().encode(ensure_pic_use), encoding="u8")
    return PIC_PATH

async def return_index() -> List[str]:
    try:
        return [key.name for key in store.get_plugin_data_dir().iterdir()]
    except ValueError as e:
        raise e from e

async def download_pic(url: str) -> Tuple[bytes, str]:
    ctx = ssl.create_default_context()
    ctx.set_ciphers('@SECLEVEL=2:ECDH+AESGCM:ECDH+CHACHA20:ECDH+AES:DHE+AES:AESGCM:!aNULL:!eNULL:!aDSS:!SHA1:!AESCCM:!PSK')
    async with AsyncClient(verify=ctx) as client:
        image = await client.get(url)
        return image.content, hashlib.md5(image.content).hexdigest()
    
async def save_pic(arg: str, path: Optional[Path] = None, url: Optional[str] = None):
    assert arg != "" and arg is not None
    QUO_DIR = store.get_plugin_data_dir() / arg
    if not QUO_DIR.exists():
        QUO_DIR.mkdir(parents=False)
    if path is not None:
        path.rename(QUO_DIR / path.name)
    elif url is not None:
        raw_bytes, md5_hex = await download_pic(url)
        PIC_PATH = QUO_DIR / str(md5_hex + ".jpg")
        PIC_PATH.write_bytes(raw_bytes)

async def save_pic_audit(arg: str, sender: str, path: Optional[Path] = None, url: Optional[str] = None):
    assert arg != "" and arg is not None
    list_return = [key.name for key in (store.get_plugin_cache_dir()).glob("*@" + sender + "@*")]
    if len(list_return) != 0:
        raise AlreadyExistsError()
    if path is not None:
        path.rename(store.get_plugin_cache_file(
            str(arg + "@" + sender + "@" + path.name + path.suffix)
        ))
    elif url is not None:
        image_bytes, md5_hex = await download_pic(url)
        store.get_plugin_cache_file(
            str(arg + "@" + sender + "@" + md5_hex + ".jpg")
        ).write_bytes(image_bytes)

async def rename_pic(path: Path):
    assert path is not None
    QUO_DIR = store.get_plugin_data_dir() / path.name.split("@", -1)[0]
    if not QUO_DIR.exists():
        QUO_DIR.mkdir(parents=False)
    NEW_PATH = QUO_DIR / path.name.split("@", -1)[2]
    path.rename(NEW_PATH)

async def audit() -> Optional[Path]:
    list_return = [key for key in (store.get_plugin_cache_dir()).iterdir()]
    if len(list_return) == 0:
        return None
    randompic = random.choice(list_return)
    return randompic

async def return_symlink() -> Dict[Path, Path]:
    return {dir : dir.readlink() for dir in store.get_plugin_data_dir().iterdir() if dir.is_symlink()}

async def create_symlink(dir: str, target: str):
    SYMLINK_PATH = store.get_plugin_data_dir() / dir
    assert not SYMLINK_PATH.exists()
    TGT_PATH = store.get_plugin_data_dir() / target
    SYMLINK_PATH.symlink_to(TGT_PATH.name, True)

async def del_symlink(arg: str):
    SYMLINK_PATH = store.get_plugin_data_dir() / arg
    assert SYMLINK_PATH.exists() and SYMLINK_PATH.is_symlink()
    SYMLINK_PATH.unlink()
