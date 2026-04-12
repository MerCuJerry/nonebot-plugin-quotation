from nonebot import logger, require
from pathlib import Path
from json import JSONEncoder, JSONDecoder
import random
from typing import Optional, List, Dict
from httpx import AsyncClient
import ssl
import hashlib
require("nonebot_plugin_localstore")
import nonebot_plugin_localstore as store  # noqa: E402

QUO_PATH = store.get_plugin_data_dir()

def init_quotation() -> bool:
    try:
        for QUO_DIR in QUO_PATH.iterdir():
            if not QUO_DIR.is_symlink():
                store.get_plugin_cache_file(str(QUO_DIR.name + ".json")).write_text(
                    JSONEncoder().encode( [key.name for key in QUO_DIR.iterdir()] ),
                    encoding="u8",
                )
        return True
    except IOError:
        return False


def send_quo(args: str) -> Path:
    PIC_DIR = QUO_PATH / args
    ENSURE_THIS_PATH =  store.get_plugin_cache_file(str(args + ".json")) if not PIC_DIR.is_symlink() else  store.get_plugin_cache_file(str(PIC_DIR.readlink().name + ".json"))
    ensure_pic_use: List[str] = JSONDecoder().decode(ENSURE_THIS_PATH.read_text(encoding="u8"))
    try:
        randompic = random.choice(ensure_pic_use)
    except IndexError:
        ensure_pic_use = [key.name for key in PIC_DIR.iterdir()]
        randompic = random.choice(ensure_pic_use)
    PIC_PATH : Path = PIC_DIR / randompic
    randompictmp : str = randompic.replace(' ','').replace('-','').replace('_','')
    if not randompictmp.__eq__(randompic):
        PIC_PATH_NEW = PIC_DIR / randompictmp
        PIC_PATH = PIC_PATH.rename(PIC_PATH_NEW)
    ensure_pic_use.remove(randompic)
    ENSURE_THIS_PATH.write_text(JSONEncoder().encode(ensure_pic_use), encoding="u8")
    return PIC_PATH

def return_index() -> List[str]:
    try:
        list_return = [key.name for key in QUO_PATH.iterdir()]
        return list_return
    except ValueError as e:
        raise e from e

async def save_pic(arg: str, url: str) -> bool:
    try:
        assert arg != "" and arg is not None
        PIC_DIR = QUO_PATH / arg
        if not PIC_DIR.exists():
            PIC_DIR.mkdir(parents=True)
        ctx = ssl.create_default_context()
        ctx.set_ciphers('@SECLEVEL=2:ECDH+AESGCM:ECDH+CHACHA20:ECDH+AES:DHE+AES:AESGCM:!aNULL:!eNULL:!aDSS:!SHA1:!AESCCM:!PSK')
        async with AsyncClient(verify=ctx) as client:
            image_bytes = await client.get(url)
            md5 = hashlib.md5()
            md5.update(image_bytes.content)
            PIC_PATH = PIC_DIR / str(md5.hexdigest() + ".jpg")
            PIC_PATH.write_bytes(image_bytes.content)
            return True
    except Exception as e:
        logger.warning(e)
        return False

async def save_pic_audit(arg: str, url: str, sender: str) -> bool:
    try:
        assert arg != "" and arg is not None
        list_return = [key.name for key in (store.get_plugin_cache_dir()).glob("*@" + sender + "@*")]
        if len(list_return) != 0:
            return False
        ctx = ssl.create_default_context()
        ctx.set_ciphers('@SECLEVEL=2:ECDH+AESGCM:ECDH+CHACHA20:ECDH+AES:DHE+AES:AESGCM:!aNULL:!eNULL:!aDSS:!SHA1:!AESCCM:!PSK')
        async with AsyncClient(verify=ctx) as client:
            image_bytes = await client.get(url)
            md5 = hashlib.md5()
            md5.update(image_bytes.content)
            store.get_plugin_cache_file(
                str(arg + "@" + sender + "@" + md5.hexdigest() + ".jpg")
            ).write_bytes(image_bytes.content)
            return True
    except Exception as e:
        logger.warning(e)
        return False

async def rename_pic(arg: Path) -> bool:
    try:
        assert arg is not None
        PIC_DIR = QUO_PATH / arg.name.split("@", -1)[0]
        if not PIC_DIR.exists():
            PIC_DIR.mkdir(parents=True)
        NEW_PATH = PIC_DIR / arg.name.split("@", -1)[2]
        arg.rename(NEW_PATH)
        return True
    except Exception as e:
        logger.warning(e)
        return False

async def return_audit() -> List[Path]:
    try:
        list_return = [key for key in (store.get_plugin_cache_dir()).iterdir()]
        return list_return
    except Exception as e:
        logger.warning(e)
        raise e from BaseException("Quotation Plugin: return_audit error")

async def audit() -> Optional[Path]:
    try:
        list_return = await return_audit()
        if len(list_return) == 0:
            return None
        randompic = random.choice(list_return)
        return randompic
    except Exception as e:
        logger.warning(e)
        raise e from BaseException("Quotation Plugin: audit error")

def return_symlink() -> Dict[Path, Path]:
    return {dir : dir.readlink() for dir in QUO_PATH.iterdir() if dir.is_symlink()}

def create_symlink(dir: str, target: str):
    SYMLINK_PATH = QUO_PATH / dir
    assert not SYMLINK_PATH.exists()
    TGT_PATH = QUO_PATH / target
    SYMLINK_PATH.symlink_to(TGT_PATH.name, True)

def del_symlink(arg: str):
    SYMLINK_PATH = QUO_PATH / arg
    assert SYMLINK_PATH.exists() and SYMLINK_PATH.is_symlink()
    SYMLINK_PATH.unlink()
