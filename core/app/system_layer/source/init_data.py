"""
系统初始化数据
- 菜单管理
- 角色管理
- 用户管理
- Casbin 权限策略
"""

from sqlalchemy import select

from ..models.menu import Menu, MenuClassify
from ..models.role import Role
from ..models.user import User
from ..models.api import API
from ..models.casbin import CasbinRule
from core import base


class MenuSource(base.Assembly):
    """菜单初始化"""

    async def initialize(self):
        """初始化菜单数据（使用嵌套结构，按层级插入）"""
        # 嵌套结构的菜单数据
        menu_tree = [
            {
                "name": "后台菜单",
                "path": "/",
                "code": "backend_system",
                "icon": "icon-zuzhitixijishishifangan",
                "redirect": "",
                "active": "",
                "component": "",
                "link": "",
                "is_hidden": False,
                "is_keep_alive": False,
                "order": 100,
                "classify": MenuClassify.DIRECTORY,
                "children": [
                    {
                        "name": "用户管理",
                        "path": "/userSystem/:page*",
                        "code": "userSystem",
                        "icon": "icon-wode",
                        "redirect": "",
                        "active": "",
                        "component": "/subsystem/userSystem",
                        "link": "",
                        "is_hidden": False,
                        "is_keep_alive": False,
                        "order": 100,
                        "classify": MenuClassify.DIRECTORY,
                        "children": [
                            {
                                "name": "菜单列表",
                                "path": "/menu/list",
                                "code": "user_system_menu",
                                "icon": "icon-wendangguanli1",
                                "redirect": "",
                                "active": "",
                                "component": "/menu/index",
                                "link": "",
                                "is_hidden": False,
                                "is_keep_alive": False,
                                "order": 100,
                                "classify": MenuClassify.MENU,
                            },
                            {
                                "name": "角色列表",
                                "path": "/role/list",
                                "code": "user_system_role",
                                "icon": "icon-anquanjiandujiancha",
                                "redirect": "",
                                "active": "",
                                "component": "/role/index",
                                "link": "",
                                "is_hidden": False,
                                "is_keep_alive": False,
                                "order": 99,
                                "classify": MenuClassify.MENU,
                            },
                            {
                                "name": "用户列表",
                                "path": "/user/list",
                                "code": "user_system_user",
                                "icon": "icon-yiwen",
                                "redirect": "",
                                "active": "",
                                "component": "/user/index",
                                "link": "",
                                "is_hidden": False,
                                "is_keep_alive": False,
                                "order": 98,
                                "classify": MenuClassify.MENU,
                            },
                            {
                                "name": "后台接口列表",
                                "path": "/backendRoute/list",
                                "code": "user_system_backend_route",
                                "icon": "icon-zhuangpeishijianzhu",
                                "redirect": "",
                                "active": "",
                                "component": "/backendRoute/index",
                                "link": "",
                                "is_hidden": False,
                                "is_keep_alive": False,
                                "order": 97,
                                "classify": MenuClassify.MENU,
                            },
                        ],
                    },
                ],
            },
            {
                "name": "前台菜单",
                "path": "/",
                "code": "front_desk_system",
                "icon": "",
                "redirect": "",
                "active": "",
                "component": "",
                "link": "",
                "is_hidden": False,
                "is_keep_alive": False,
                "order": 99,
                "classify": MenuClassify.DIRECTORY,
                "children": [
                    {
                        "name": "智能体广场",
                        "path": "/intelligentAgentSquare/:page*",
                        "code": "intelligentAgentSquare",
                        "icon": "icon-BIMjishujianguan",
                        "redirect": "",
                        "active": "",
                        "component": "/subsystem/intelligentAgentSquare",
                        "link": "",
                        "is_hidden": False,
                        "is_keep_alive": False,
                        "order": 100,
                        "classify": MenuClassify.DIRECTORY,
                        "children": [
                            {
                                "name": "对话",
                                "path": "/agent/chat",
                                "code": "agent_chat",
                                "icon": "icon-fuwuguanlizhongxin-fill",
                                "redirect": "",
                                "active": "",
                                "component": "/chat/index",
                                "link": "",
                                "is_hidden": True,
                                "is_keep_alive": False,
                                "order": 99,
                                "classify": MenuClassify.MENU,
                            },
                            {
                                "name": "智能体广场",
                                "path": "/agent/list",
                                "code": "agent_list",
                                "icon": "icon-moxingzhongxin",
                                "redirect": "",
                                "active": "",
                                "component": "/agent/index",
                                "link": "",
                                "is_hidden": True,
                                "is_keep_alive": False,
                                "order": 0,
                                "classify": MenuClassify.MENU,
                            },
                        ],
                    },
                ],
            },
            {
                "name": "App菜单",
                "path": "/",
                "code": "app_system",
                "icon": "",
                "redirect": "",
                "active": "",
                "component": "",
                "link": "",
                "is_hidden": False,
                "is_keep_alive": False,
                "order": 98,
                "classify": MenuClassify.DIRECTORY,
                "children": [],
            },
        ]

        try:
            async with self.get_db() as db:
                # 用于存储 code -> id 的映射
                code_to_id = {}

                # 递归插入菜单
                async def insert_menu(menu_data: dict, parent_id: int | None = None):
                    # 检查是否已存在
                    existing = await db.scalar(select(Menu).where(Menu.code == menu_data["code"]))

                    if existing:
                        code_to_id[menu_data["code"]] = existing.id
                    else:
                        menu = Menu(
                            name=menu_data["name"],
                            path=menu_data["path"],
                            code=menu_data["code"],
                            parent_id=parent_id,
                            icon=menu_data.get("icon", ""),
                            redirect=menu_data.get("redirect", ""),
                            active=menu_data.get("active", ""),
                            component=menu_data.get("component", ""),
                            link=menu_data.get("link", ""),
                            is_hidden=menu_data.get("is_hidden", False),
                            is_keep_alive=menu_data.get("is_keep_alive", False),
                            order=menu_data.get("order", 0),
                            classify=menu_data["classify"],
                        )
                        db.add(menu)
                        await db.flush()  # 获取生成的 ID
                        code_to_id[menu_data["code"]] = menu.id

                    # 插入子菜单
                    for child in menu_data.get("children", []):
                        await insert_menu(child, code_to_id[menu_data["code"]])

                # 开始插入
                for root_menu in menu_tree:
                    await insert_menu(root_menu)

                await db.commit()
            self.S().info(f"{Menu.__tablename__} 表数据初始化成功")

        except Exception as e:
            self.S().error(f"{Menu.__tablename__} 表数据初始化失败: {str(e)}")

    async def check_data_exist(self) -> bool:
        """检查是否存在 code='backend_system' 的记录"""
        async with self.get_db() as db:
            res = await db.scalar(select(Menu).where(Menu.code == "backend_system"))
        return res is not None


class RoleSource(base.Assembly):
    """角色初始化"""

    async def initialize(self):
        """初始化角色数据"""
        roles = [
            Role(
                name="超级管理员",
                code="admin",
                description="拥有所有权限",
            ),
        ]

        try:
            async with self.get_db() as db:
                for role in roles:
                    existing = await db.scalar(select(Role).where(Role.code == role.code))
                    if not existing:
                        db.add(role)
                await db.commit()
            self.S().info(f"{Role.__tablename__} 表数据初始化成功")

        except Exception as e:
            self.S().error(f"{Role.__tablename__} 表数据初始化失败: {str(e)}")

    async def check_data_exist(self) -> bool:
        """检查是否存在 code='admin' 的记录"""
        async with self.get_db() as db:
            res = await db.scalar(select(Role).where(Role.code == "admin"))
        return res is not None


class UserSource(base.Assembly):
    """用户初始化"""

    async def initialize(self):
        """初始化用户数据（超级管理员）"""
        # 先获取角色ID
        role_id = 1
        async with self.get_db() as db:
            role = await db.scalar(select(Role).where(Role.code == "admin"))
            if role:
                role_id = role.id

        users = [
            User(
                name="超级管理员",
                login="admin",
                password=self.md5v(self.get_viper().get_string("system.default-password").encode()),
                role_id=role_id,
            )
        ]

        try:
            async with self.get_db() as db:
                for user in users:
                    existing = await db.scalar(select(User).where(User.login == user.login))
                    if not existing:
                        db.add(user)
                await db.commit()
            self.S().info(f"{User.__tablename__} 表数据初始化成功")

        except Exception as e:
            self.S().error(f"{User.__tablename__} 表数据初始化失败: {str(e)}")

    async def check_data_exist(self) -> bool:
        """检查是否存在 login='admin' 的记录"""
        async with self.get_db() as db:
            res = await db.scalar(select(User).where(User.login == "admin"))
        return res is not None


class CasbinSource(base.Assembly):
    """Casbin 权限策略初始化"""

    async def initialize(self):
        """初始化 Casbin 权限策略（超级管理员拥有所有权限）"""
        # 获取超级管理员角色的 code
        role_code = "admin"

        # 菜单权限策略 [role_code, 'menu', menu_code, "all"]
        # v2 使用菜单数据的 code 字段
        menu_policies = [
            # 后台菜单
            CasbinRule(ptype="p", v0=role_code, v1="menu", v2="backend_system", v3="all"),
            CasbinRule(ptype="p", v0=role_code, v1="menu", v2="userSystem", v3="all"),
            CasbinRule(ptype="p", v0=role_code, v1="menu", v2="user_system_menu", v3="all"),
            CasbinRule(ptype="p", v0=role_code, v1="menu", v2="user_system_role", v3="all"),
            CasbinRule(ptype="p", v0=role_code, v1="menu", v2="user_system_user", v3="all"),
            CasbinRule(
                ptype="p", v0=role_code, v1="menu", v2="user_system_backend_route", v3="all"
            ),
            # 前台菜单
            CasbinRule(ptype="p", v0=role_code, v1="menu", v2="front_desk_system", v3="all"),
            CasbinRule(ptype="p", v0=role_code, v1="menu", v2="intelligentAgentSquare", v3="all"),
            CasbinRule(ptype="p", v0=role_code, v1="menu", v2="agent_chat", v3="all"),
            CasbinRule(ptype="p", v0=role_code, v1="menu", v2="agent_list", v3="all"),
            # App菜单
            CasbinRule(ptype="p", v0=role_code, v1="menu", v2="app_system", v3="all"),
        ]

        # API 权限策略 [role_code, 'api', api_path, method]
        # v2 是后端路由路径
        api_policies = [
            # 菜单管理
            CasbinRule(ptype="p", v0=role_code, v1="api", v2="/menu/list", v3="GET"),
            CasbinRule(ptype="p", v0=role_code, v1="api", v2="/menu/tree", v3="GET"),
            CasbinRule(ptype="p", v0=role_code, v1="api", v2="/menu/{id}", v3="GET"),
            CasbinRule(ptype="p", v0=role_code, v1="api", v2="/menu/create", v3="POST"),
            CasbinRule(ptype="p", v0=role_code, v1="api", v2="/menu/update", v3="PUT"),
            CasbinRule(ptype="p", v0=role_code, v1="api", v2="/menu/delete", v3="DELETE"),
            # 角色管理
            CasbinRule(ptype="p", v0=role_code, v1="api", v2="/role/list", v3="GET"),
            CasbinRule(ptype="p", v0=role_code, v1="api", v2="/role/get_role_permission", v3="GET"),
            CasbinRule(ptype="p", v0=role_code, v1="api", v2="/role/{id}", v3="GET"),
            CasbinRule(ptype="p", v0=role_code, v1="api", v2="/role/create", v3="POST"),
            CasbinRule(ptype="p", v0=role_code, v1="api", v2="/role/update", v3="PUT"),
            CasbinRule(ptype="p", v0=role_code, v1="api", v2="/role/delete", v3="DELETE"),
            CasbinRule(ptype="p", v0=role_code, v1="api", v2="/role/update_role_menu", v3="POST"),
            CasbinRule(ptype="p", v0=role_code, v1="api", v2="/role/update_role_api", v3="POST"),
            # 用户管理
            CasbinRule(ptype="p", v0=role_code, v1="api", v2="/user/list", v3="GET"),
            CasbinRule(
                ptype="p", v0=role_code, v1="api", v2="/user/according_token_obtain", v3="GET"
            ),
            CasbinRule(
                ptype="p", v0=role_code, v1="api", v2="/user/according_token_basic", v3="GET"
            ),
            CasbinRule(ptype="p", v0=role_code, v1="api", v2="/user/{id}", v3="GET"),
            CasbinRule(ptype="p", v0=role_code, v1="api", v2="/user/create", v3="POST"),
            CasbinRule(ptype="p", v0=role_code, v1="api", v2="/user/update", v3="PUT"),
            CasbinRule(ptype="p", v0=role_code, v1="api", v2="/user/update_information", v3="PUT"),
            CasbinRule(ptype="p", v0=role_code, v1="api", v2="/user/delete", v3="DELETE"),
        ]

        policies = menu_policies + api_policies

        try:
            async with self.get_db() as db:
                for policy in policies:
                    # 检查是否已存在
                    existing = await db.scalar(
                        select(CasbinRule).where(
                            CasbinRule.ptype == policy.ptype,
                            CasbinRule.v0 == policy.v0,
                            CasbinRule.v1 == policy.v1,
                            CasbinRule.v2 == policy.v2,
                            CasbinRule.v3 == policy.v3,
                        )
                    )
                    if not existing:
                        db.add(policy)
                await db.commit()
            self.S().info(f"{CasbinRule.__tablename__} 表数据初始化成功")

        except Exception as e:
            self.S().error(f"{CasbinRule.__tablename__} 表数据初始化失败: {str(e)}")

    async def check_data_exist(self) -> bool:
        """检查是否存在 policy"""
        async with self.get_db() as db:
            res = await db.scalar(
                select(CasbinRule).where(
                    CasbinRule.ptype == "p",
                    CasbinRule.v0 == "admin",
                    CasbinRule.v1 == "menu",
                    CasbinRule.v2 == "backend_system",
                )
            )
        return res is not None


# 创建单例实例
menu_source = MenuSource()
role_source = RoleSource()
user_source = UserSource()
casbin_source = CasbinSource()
