from nonebot import require, get_plugin_config
from nonebot.plugin import PluginMetadata, inherit_supported_adapters
from nonebot.typing import T_State
from nonebot.adapters import Event, MessageTemplate, Message, Bot
from nonebot.params import Arg, Received, Depends
from nonebot.matcher import Matcher
from nonebot.message import handle_event
from pydantic import BaseModel
from .quotation import (
    init_quotation,
    send_quo,
    return_index,
    save_pic,
    return_symlink,
    del_symlink,
    create_symlink,
    audit,
    save_pic_audit,
    rename_pic,
)

from nepattern import AnyString
from arclet.alconna import Alconna, CommandMeta, Args
require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import on_alconna, Match, get_message_id, AlconnaMatch  # noqa: E402
from nonebot_plugin_alconna.uniseg import Image, UniMessage, Reply  # noqa: E402
from nonebot_plugin_alconna.extension import Extension  # noqa: E402

class Config(BaseModel):
    trusted_user: list = []

__version__ = "0.1.0"
__plugin_meta__ = PluginMetadata(
    name="Quotation",
    description="简单的语录插件",
    usage="",
    type="application",
    homepage="https://github.com/MerCuJerry/nonebot-plugin-batitle",
    config=Config,
    supported_adapters=inherit_supported_adapters("nonebot_plugin_alconna"),
    extra={
        "version": __version__,
        "author": "MerCuJerry <mercujerry@gmail.com>",
    },
)

async def checker(person: Match[str]) -> bool:
    try:
        return_index().index(person.result)
    except ValueError:
        return False
    else:
        return True

quote_matcher = on_alconna(
    Alconna("来点", Args["person", AnyString], meta=CommandMeta(description="来一张群友的怪话", compact=True)),
    after_rule=checker,
    priority=2,
    block=True)

class TrustedUserPermissionExtension(Extension):
    @property
    def priority(self) -> int:
        return 10

    @property
    def id(self) -> str:
        return "TrustedUserPermissionExtension"
    
    async def permission_check(self, bot, event, medium) -> bool:
        return event.get_user_id() in bot.config.superusers or event.get_user_id() in get_plugin_config(Config).trusted_user

quote_update = on_alconna(
    Alconna("更新语录", meta=CommandMeta(description="刷新怪话缓存", hide=True, hide_shortcut=True)),
    extensions=[TrustedUserPermissionExtension()],
    use_cmd_start=True,
    priority=5,
    block=True)

quote_query = on_alconna(
    Alconna("查询语录", meta=CommandMeta(description="查询怪话", hide=True, hide_shortcut=True)),
    extensions=[TrustedUserPermissionExtension()],
    use_cmd_start=True,
    priority=5,
    block=True)

quote_add = on_alconna(
    Alconna("添加", Args["person", str], meta=CommandMeta(description="添加一张群友的怪话", compact=True)),
    use_cmd_start=True,
    priority=5,
    block=True)

quote_audit = on_alconna(
    Alconna("审查语录", meta=CommandMeta(description="审查怪话", hide=True, hide_shortcut=True)),
    extensions=[TrustedUserPermissionExtension()],
    use_cmd_start=True,
    priority=5,
    block=True)

symlink = on_alconna(
    Alconna("查询语录别名", meta=CommandMeta(description="查询语录别名", hide=True, hide_shortcut=True)),
    extensions=[TrustedUserPermissionExtension()],
    use_cmd_start=True,
    priority=5,
    block=True)

symlink_create = on_alconna(
    Alconna(
        "添加语录别名",
        Args["name", AnyString]["person", return_index()].separate('>'),
        meta=CommandMeta(description="添加语录别名", hide=True, hide_shortcut=True, compact=True)
    ),
    extensions=[TrustedUserPermissionExtension()],
    use_cmd_start=True,
    priority=2,
    block=True)

async def checker_symlink(person: Match[str]) -> bool:
    try:
        [k.name for k in return_symlink().keys()].index(person.result)
    except ValueError:
        return False
    else:
        return True
symlink_del = on_alconna(
    Alconna(
        "删除语录别名",
        Args["person", AnyString],
        meta=CommandMeta(description="删除语录别名", hide=True, hide_shortcut=True, compact=True)
    ),
    after_rule=checker_symlink,
    extensions=[TrustedUserPermissionExtension()],
    use_cmd_start=True,
    priority=2,
    block=True)

@quote_matcher.handle()
async def qmhandler(person : Match[str], state: T_State):
    path = send_quo(person.result)
    state["quotation_last_path"] = path
    await UniMessage([Reply(get_message_id()), Image(raw=path.read_bytes())]).send()

async def quote_checker(bot: Bot, event: Event = Received("delete_quote")) -> Event | None:
    if str(event.get_message()) == "删除语录" and (event.get_user_id() in bot.config.superusers or event.get_user_id() in get_plugin_config(Config).trusted_user):
        return event
    else:
        await handle_event(bot, event)

@quote_matcher.receive("delete_quote")
async def quotereceive(matcher: Matcher, state: T_State, event: Event = Depends(quote_checker)):
    try:
        state["quotation_last_path"].unlink()
        await matcher.finish("删除成功")
    except FileNotFoundError:
        await matcher.finish("文件未找到")
        

@quote_update.handle()
async def quoteupdatehandler(matcher: Matcher):
    if init_quotation():
        await matcher.finish("更新完毕")
    else:
        await matcher.finish("更新错误")

@quote_query.handle()
async def queryhandler(matcher: Matcher):
    query_sep = '/'
    query_head = '当前语录列表： \n'
    await matcher.finish(query_head+query_sep.join(return_index()))

# quote add
@quote_add.handle()
async def addhandler(person : Match[str], state: T_State):
    state["add_path"] = person.result

@quote_add.got("arg", prompt=MessageTemplate("请发送要添加至{add_path}的图片"))
async def addgot(matcher: Matcher, bot: Bot, event: Event, state: T_State, arg: Message = Arg()):
    if "image" not in arg:
        await matcher.finish("添加出错请重新添加 (回复中需要包含至少一张图片)")
    if(event.get_user_id() in bot.config.superusers or event.get_user_id() in get_plugin_config(Config).trusted_user):
        for pic in arg.get("image"):
            image_url = pic.data["url"]
        ok = await save_pic(state["add_path"], image_url) # type: ignore
        if ok:
            await matcher.finish("添加成功")
        else:
            await matcher.finish("添加失败了哦，请重新添加")
    else:
        for pic in arg.get("image"):
            image_url = pic.data["url"]
        ok = await save_pic_audit(state["add_path"], image_url, event.get_user_id()) # type: ignore
        if ok:
            await matcher.finish("添加成功，等待审查")
        else:
            await matcher.finish("你已经有待审查的语录了哦，请等待审查结果")

# audit 
@quote_audit.handle()
async def audithandler(matcher: Matcher, state: T_State):
    audit_path = await audit()
    if audit_path is not None:
        state["audit_path"] = audit_path
        state["audit_path_name"] = audit_path.name.split("@", -1)[0]
        await UniMessage(Image(raw=audit_path.read_bytes())).send()
    else:
        await matcher.finish("没有待审查的语录了哦")

@quote_audit.got("arg_audit", prompt=MessageTemplate("该图片添加到{audit_path_name}，请输入审查结果，发送“通过”以通过审查，发送“拒绝”以拒绝审查"))
async def auditgot(matcher: Matcher, state: T_State, arg_audit: Message = Arg()):
    if not state["audit_path"].is_file():
        await matcher.finish("需要审查的语录已经被审查")
    if str(arg_audit) == "通过":
        ok = await rename_pic(state["audit_path"])
        if ok:
            await matcher.finish("审查通过，已添加至语录")
        else:
            await matcher.finish("审查通过，但添加至语录失败了")
    elif str(arg_audit) == "拒绝":
        state["audit_path"].unlink()
        await matcher.finish("审查拒绝，已删除待审查语录")
    else:
        await matcher.finish("输入有误，请重新输入")

# symlink
@symlink.handle()
async def symlinkhandler(matcher: Matcher):
    symlink_dict = return_symlink()
    formatted_str = "\n".join(f"{key.name} --> {value.name}" for key, value in symlink_dict.items())
    await matcher.finish(formatted_str)

@symlink_create.handle()
async def symlinkChandler(matcher: Matcher, name: Match[str] = AlconnaMatch("name"), person: Match[str] = AlconnaMatch("person")):
    try:
        create_symlink(name.result, person.result)
        await matcher.send("添加成功")
    except AssertionError:
        await matcher.send("存在这样的语录别名或语录")
    except TypeError:
        await matcher.send("请检查命令格式!")
    except Exception:
        await matcher.send("出错了...怎么回事呢?")
    finally:
        await matcher.finish()

@symlink_del.handle()
async def symlinkDhandler(matcher: Matcher, person: Match[str]):
    try:
        del_symlink(person.result)
        await matcher.send("删除成功")
    except AssertionError:
        await matcher.send("没有那样的别名哦")
    except Exception:
        await matcher.send("出错了...怎么回事呢?")
    finally:
        await matcher.finish()