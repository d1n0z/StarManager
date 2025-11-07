import json
from pathlib import Path
from typing import Dict, List, Union

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from vk_api import vk_api
from vkbottle import API

settings_path = Path(__file__).parent


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class CommandsConfig(BaseModel):
    commands: Dict[str, int]
    pm: List[str]
    premium: List[str]
    cooldown: Dict[str, int]
    descriptions: Dict[str, str]
    prefix: List[str]
    lvlbanned: List[str]


class LeaguesConfig(BaseModel):
    required_level: List[int]
    leagues: List[str]
    creategroup_bonus: List[int]
    cmd_bonus: List[int]


class SettingsDefaultConfig(BaseModel):
    defaults: Dict[str, Dict[str, int]]


class SettingsMetaConfig(BaseModel):
    positions: Dict[str, Dict[str, List[str]]]
    countable: List[str]
    countable_multiple_arguments: List[str]
    countable_no_punishment: List[str]
    countable_no_category: List[str]
    countable_punishment_no_delete_message: List[str]
    countable_special_limits: Dict[str, List[int]]
    defaults: Dict[str, Dict[str, Union[int, str]]]
    premium: List[str]
    countable_changemenu: Dict[str, List[Dict[str, Union[str, List[str]]]]]
    preset_buttons: Dict[str, List[Dict[str, Union[int, str]]]]
    alt_to_delete: List[str]
    subcats: Dict[str, str]

    @field_validator("countable_special_limits", mode="before")
    def parse_ranges(cls, value: dict):
        def parse_range(v):
            if isinstance(v, str) and v.startswith("range"):
                try:
                    return list(eval(v))
                except Exception:
                    raise ValueError(f"Invalid range string: {v}")
            return v

        return {k: parse_range(v) for k, v in value.items()}


class PremiumMenuConfig(BaseModel):
    default: Dict[str, Union[bool, None]]
    turn: List[str]


class ShopConfig(BaseModel):
    xp: Dict[int, Dict[str, int]]
    bonuses: Dict[str, Dict[str, Union[int, str]]]


class GoogleThreatsConfig(BaseModel):
    threats: Dict[str, str]


class NsfwCategoriesConfig(BaseModel):
    categories: List[str]


class PremiumCostConfig(BaseModel):
    cost: Dict[int, int]


class ImportSettingsConfig(BaseModel):
    default: Dict[str, bool]


class VKSettings(BaseSettings):
    token_group: str
    token_implicit_flow: str
    service_token: str
    group_id: int
    app_id: int
    app_secret: str
    callback_secret: str
    callback_confirmation_code: str


class ServiceSettings(BaseSettings):
    daily_to: int
    mathgiveaways_to: int
    devs: List[int] = Field(default_factory=list)
    admins: List[int] = Field(default_factory=list)
    main_devs: List[int] = Field(default_factory=list)
    path: str
    farm_post_id: int
    premium_bonus_post_id: int
    photo_not_found: str
    contact_admin: str
    too_old_last_seen_in: List[int] = Field(default_factory=list)


class DatabaseSettings(BaseSettings):
    user: str
    password: str
    name: str
    host: str
    port: int


class TelegramSettings(BaseSettings):
    token: str
    bot_username: str
    chat_id: int
    backup_thread_id: int
    premium_thread_id: int
    newchat_thread_id: int
    transfer_thread_id: int
    shop_thread_id: int
    audio_thread_id: int
    bonus_thread_id: int
    duel_thread_id: int
    rps_thread_id: int
    scheduler_thread_id: int
    reports_chat_id: int
    reports_new_thread_id: int
    reports_archive_thread_id: int
    public_chat_id: int
    public_giveaway_thread_id: int
    api_hash: str
    api_id: int
    webhook_url: str
    admins: List[int] = Field(default_factory=list)


class YookassaSettings(BaseSettings):
    merchant_id: int
    token: str


class YandexSettings(BaseSettings):
    token: str


class GoogleSettings(BaseSettings):
    token: str


class SocialsSettings(BaseSettings):
    email: str
    vk: str
    premium_info: str
    tg: str


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_nested_delimiter="__", extra="allow"
    )

    vk: VKSettings
    service: ServiceSettings
    database: DatabaseSettings
    telegram: TelegramSettings
    yookassa: YookassaSettings
    yandex: YandexSettings
    google: GoogleSettings
    socials: SocialsSettings

    commands: CommandsConfig = CommandsConfig(
        **load_json(settings_path / "commands.json")
    )
    leagues: LeaguesConfig = LeaguesConfig(**load_json(settings_path / "leagues.json"))
    lvl_names: List[str] = load_json(settings_path / "lvl_names.json")
    settings_default: SettingsDefaultConfig = SettingsDefaultConfig(
        **load_json(settings_path / "settings_default.json")
    )
    settings_alt: SettingsDefaultConfig = SettingsDefaultConfig(
        **load_json(settings_path / "settings_alt.json")
    )
    settings_meta: SettingsMetaConfig = SettingsMetaConfig(
        **load_json(settings_path / "settings_meta.json")
    )
    premium_menu: PremiumMenuConfig = PremiumMenuConfig(
        **load_json(settings_path / "premium_menu.json")
    )
    shop: ShopConfig = ShopConfig(**load_json(settings_path / "shop.json"))
    google_threats: GoogleThreatsConfig = GoogleThreatsConfig(
        threats=load_json(settings_path / "google_threats.json")
    )
    nsfw_categories: NsfwCategoriesConfig = NsfwCategoriesConfig(
        categories=load_json(settings_path / "nsfw_categories.json")
    )
    premium_cost: PremiumCostConfig = PremiumCostConfig(
        cost=load_json(settings_path / "premium_cost.json")
    )
    import_settings: ImportSettingsConfig = ImportSettingsConfig(
        default=load_json(settings_path / "import_settings_default.json")
    )


settings = Settings()  # type: ignore

api = API(settings.vk.token_group)
vk_api_session = vk_api.VkApi(token=settings.vk.token_group, api_version="5.199")
service_vk_api_session = vk_api.VkApi(
    token=settings.vk.service_token, api_version="5.199"
)

DATABASE_STR = f"postgres://{settings.database.user}:{settings.database.password}@{settings.database.host}:{settings.database.port}/{settings.database.name}"

sitedata = {
    "email": settings.socials.email,
    "vk": settings.socials.vk,
    "vk_contact": settings.socials.vk.replace(".com", ".me"),
    "vk_preminfo": settings.socials.premium_info,
    "tg": settings.socials.tg,
    "high": f"{settings.premium_cost.cost[180]}",
    "medium": f"{settings.premium_cost.cost[90]}",
    "low": f"{settings.premium_cost.cost[30]}",
    "premiumchat": "199",
}

database_config = {
    "connections": {"default": {"engine": "src.StarManager.core.tortoise_pool", "credentials": {"database": settings.database.name}}},
    "apps": {
        "models": {
            "models": ["StarManager.core.tables", "aerich.models"],
            "default_connection": "default",
        },
    },
}


__ALL__ = [
    settings,
    api,
    vk_api_session,
    service_vk_api_session,
    DATABASE_STR,
    sitedata,
    database_config,
]
