from nonebot import require, get_plugin_config, logger
from nonebot.plugin import PluginMetadata, inherit_supported_adapters
from nonebot.typing import T_State
from nonebot.adapters import Event, MessageTemplate, Message, Bot
from nonebot.params import Arg, Received, Depends
from nonebot.matcher import Matcher
from nonebot.message import handle_event
from pydantic import BaseModel, Field
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
from .quotation import AlreadyExistsError, NeedUpdateError
from typing import List

from nepattern import AnyString
from arclet.alconna import Alconna, CommandMeta, Args
require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import on_alconna, Match, AlconnaMatch, AlconnaMatcher  # noqa: E402
from nonebot_plugin_alconna.uniseg import Image, UniMessage, Reply, MsgId  # noqa: E402
from nonebot_plugin_alconna.extension import Extension  # noqa: E402

class QuotationPluginConfigModel(BaseModel):
    trusted_user: List[str] = Field(default=[], alias="quotation_trusted_user", description="受信任的用户列表，列表内用户可以直接添加语录和审查语录")

__version__ = "0.1.2.post1"
__plugin_meta__ = PluginMetadata(
    name="语录插件",
    description="基于Alconna的简单的语录插件, 支持添加语录别名以及审查用户添加的语录",
    usage="来点",
    type="application",
    homepage="https://github.com/MerCuJerry/nonebot-plugin-quotation",
    config=QuotationPluginConfigModel,
    supported_adapters=inherit_supported_adapters("nonebot_plugin_alconna"),
    extra={
        "version": __version__,
        "author": "MerCuJerry <mercujerry@gmail.com>",
    },
)

quotation_plugin_config: QuotationPluginConfigModel = get_plugin_config(QuotationPluginConfigModel)

async def checker(person: Match[str]) -> bool:
    try:
        (await return_index()).index(person.result)
    except ValueError:
        return False
    else:
        return True

quotation_matcher = on_alconna(
    Alconna("来点", Args["person", AnyString], meta=CommandMeta(description="来一张群友的怪话", compact=True)),
    after_rule=checker,
    priority=2,
    block=True)

async def perm_checker(bot: Bot, event: Event) -> bool:
    return event.get_user_id() in bot.config.superusers or event.get_user_id() in quotation_plugin_config.trusted_user

class QuotationTrustedUserPermissionExtension(Extension):
    @property
    def priority(self) -> int:
        return 10

    @property
    def id(self) -> str:
        return "QuotationTrustedUserPermissionExtension"
    
    async def permission_check(self, bot, event, medium) -> bool:
        return await perm_checker(bot, event)

quotation_update = on_alconna(
    Alconna("更新语录", meta=CommandMeta(description="刷新怪话缓存", hide=True, hide_shortcut=True)),
    extensions=[QuotationTrustedUserPermissionExtension()],
    use_cmd_start=True,
    priority=5,
    block=True)

quotation_query = on_alconna(
    Alconna("查询语录", meta=CommandMeta(description="查询怪话", hide=True, hide_shortcut=True)),
    extensions=[QuotationTrustedUserPermissionExtension()],
    use_cmd_start=True,
    priority=5,
    block=True)

quotation_add = on_alconna(
    Alconna("添加", Args["person", str]["image?", Image].separate(''), meta=CommandMeta(description="添加一张群友的怪话", compact=True)),
    use_cmd_start=True,
    priority=5,
    block=True)

quotation_audit = on_alconna(
    Alconna("审查语录", meta=CommandMeta(description="审查怪话", hide=True, hide_shortcut=True)),
    extensions=[QuotationTrustedUserPermissionExtension()],
    use_cmd_start=True,
    priority=5,
    block=True)

quotation_symlink = on_alconna(
    Alconna("查询语录别名", meta=CommandMeta(description="查询语录别名", hide=True, hide_shortcut=True)),
    extensions=[QuotationTrustedUserPermissionExtension()],
    use_cmd_start=True,
    priority=5,
    block=True)

quotation_symlink_create = on_alconna(
    Alconna(
        "添加语录别名",
        Args["name", AnyString]["person", return_index()].separate('>'),
        meta=CommandMeta(description="添加语录别名", hide=True, hide_shortcut=True, compact=True)
    ),
    extensions=[QuotationTrustedUserPermissionExtension()],
    use_cmd_start=True,
    priority=2,
    block=True)

async def checker_quotation_symlink(person: Match[str]) -> bool:
    try:
        [k.name for k in (await return_symlink()).keys()].index(person.result)
    except ValueError:
        return False
    else:
        return True

quotation_symlink_del = on_alconna(
    Alconna(
        "删除语录别名",
        Args["person", AnyString],
        meta=CommandMeta(description="删除语录别名", hide=True, hide_shortcut=True, compact=True)
    ),
    after_rule=checker_quotation_symlink,
    extensions=[QuotationTrustedUserPermissionExtension()],
    use_cmd_start=True,
    priority=2,
    block=True)

@quotation_matcher.handle()
async def qm_handler(matcher: AlconnaMatcher, person : Match[str], state: T_State, msg_id: MsgId):
    try:
        path = await send_quo(person.result)
        state["quotation_last_path"] = path
        await UniMessage([Reply(msg_id), Image(raw=path.read_bytes())]).send()
    except NeedUpdateError as e:
        await matcher.finish("语录需要更新，请先执行更新操作")
    except Exception as e:
        logger.error(e)
        await matcher.finish("发生未知错误" + str(e))

async def quotation_checker(bot: Bot, event: Event = Received("delete_quote")) -> Event | None:
    if event.get_message().extract_plain_text() == "删除语录" and await perm_checker(bot, event):
        return event
    else:
        await handle_event(bot, event)

@quotation_matcher.receive("delete_quote")
async def quotation_receive(matcher: Matcher, state: T_State, event: Event = Depends(quotation_checker)):
    try:
        state["quotation_last_path"].unlink()
        await matcher.finish("删除成功")
    except FileNotFoundError:
        await matcher.finish("文件未找到")

@quotation_update.handle()
async def quotation_update_handler(matcher: Matcher):
    try:
        await init_quotation()
    except Exception as e:
        logger.error(e)
        await matcher.finish("更新错误")
    else:
        await matcher.finish("更新完毕")

@quotation_query.handle()
async def quotation_query_handler(matcher: Matcher):
    query_sep = '/'
    query_head = '当前语录列表： \n'
    await matcher.finish(query_head+query_sep.join(await return_index()))

# quote add
@quotation_add.handle()
async def quotation_add_handler(
    matcher: AlconnaMatcher,
    bot: Bot,
    event: Event,
    msg_id: MsgId,
    person : Match[str],
    image: Match[Image]
    ):
    if image.available:
        image_result = image.result
    else:
        resp = await matcher.prompt(
            UniMessage.template("{:Reply(msg_id)}请发送要添加至{person}的图片").format(msg_id=msg_id, person=person.result),
            timeout=20
        )
        if resp is None:
            await matcher.finish("添加超时了哦，请重新添加")
        elif not resp.has(Image):
            await matcher.finish("发送的消息里没有图片哦，请重新添加")
        else:
            image_result : Image = resp.get(Image, 1)[0]
    if await perm_checker(bot, event):
        try:
            if image_result.raw:
                await save_pic(person.result, path=image_result.save())
            elif image_result.url:
                await save_pic(person.result, url=image_result.url)
        except Exception as e:
            logger.error(e)
            await matcher.finish("添加失败了哦，请重新添加")
        else:
            await matcher.finish("添加成功，已添加至语录")
    else:
        try:
            if image_result.raw:
                await save_pic_audit(person.result, event.get_user_id(), path=image_result.save())
            elif image_result.url:
                await save_pic_audit(person.result, event.get_user_id(), url=image_result.url)
        except AlreadyExistsError as e:
            logger.error(e)
            await matcher.finish("你已经有待审查的语录了哦，请等待审查结果")
        except Exception as e:
            logger.error(e)
            await matcher.finish("添加失败了哦，请重新添加")
        else:
            await matcher.finish("添加成功，等待审查")

# audit 
@quotation_audit.handle()
async def quotation_audit_handler(matcher: Matcher, state: T_State):
    try:
        audit_path = await audit()
    except Exception as _e:
        await matcher.finish("审查出错了哦，请稍后再试")
    else:
        if audit_path is not None:
            state["audit_path"] = audit_path
            state["audit_path_name"] = audit_path.name.split("@", -1)[0]
            await UniMessage(Image(raw=audit_path.read_bytes())).send()
        else:
            await matcher.finish("没有待审查的语录了哦")

@quotation_audit.got("arg_audit", prompt=MessageTemplate("该图片添加到{audit_path_name}，请输入审查结果，发送“通过”以通过审查，发送“拒绝”以拒绝审查"))
async def quotation_audit_got(matcher: Matcher, state: T_State, arg_audit: Message = Arg()):
    if not state["audit_path"].is_file():
        await matcher.finish("需要审查的语录已经被审查")
    if arg_audit.extract_plain_text() == "通过":
        try:
            await rename_pic(state["audit_path"])
        except Exception as e:
            logger.error(e)
            await matcher.finish("审查通过，但添加至语录失败了")
        else:
            await matcher.finish("审查通过，已添加至语录")
    elif arg_audit.extract_plain_text() == "拒绝":
        state["audit_path"].unlink()
        await matcher.finish("审查拒绝，已删除待审查语录")
    else:
        await matcher.finish("输入有误，请重新输入")

# quotation_symlink
@quotation_symlink.handle()
async def quotation_symlink_handler(matcher: Matcher):
    formatted_str = "\n".join(f"{key.name} --> {value.name}" for key, value in (await return_symlink()).items())
    await matcher.finish(formatted_str)

@quotation_symlink_create.handle()
async def quotation_symlink_create_handler(matcher: Matcher, name: Match[str] = AlconnaMatch("name"), person: Match[str] = AlconnaMatch("person")):
    try:
        await create_symlink(name.result, person.result)
    except AssertionError:
        await matcher.send("存在这样的语录别名或语录")
    except TypeError as e:
        logger.error(e)
        await matcher.send("请检查命令格式!")
    except OSError as e:
        logger.error(e)
        await matcher.send("创建语录别名失败," + str(e))
    except Exception as e:
        logger.error(e)
        await matcher.send("出错了..." + str(e))
    else:
        await matcher.send("添加成功")
    finally:
        await matcher.finish()

@quotation_symlink_del.handle()
async def quotation_symlink_del_handler(matcher: Matcher, person: Match[str]):
    try:
        await del_symlink(person.result)
    except AssertionError:
        await matcher.send("没有那样的别名哦")
    except Exception as e:
        logger.error(e)
        await matcher.send("出错了..." + str(e))
    else:
        await matcher.send("删除成功")
    finally:
        await matcher.finish()