from typing import Optional, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.settings import SystemSettings
from schemas.settings import SystemSettingCreate, SystemSettingUpdate
from core.exceptions import APIException


class SettingsService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_setting(self, key: str) -> Optional[SystemSettings]:
        """Retrieve a system setting by its key."""
        result = await self.session.execute(
            select(SystemSettings).filter(SystemSettings.key == key)
        )
        return result.scalars().first()

    async def get_setting_value(self, key: str, default: Any = None) -> Any:
        """Retrieve the value of a system setting by its key, with a default fallback."""
        setting = await self.get_setting(key)
        if setting:
            return self._convert_value_from_db(setting.value, setting.value_type)
        return default

    async def get_all_settings(self) -> list[SystemSettings]:
        """Retrieve all system settings."""
        result = await self.session.execute(
            select(SystemSettings)
        )
        return result.scalars().all()

    async def create_setting(self, setting_in: SystemSettingCreate) -> SystemSettings:
        """Create a new system setting."""
        db_setting = SystemSettings(
            key=setting_in.key,
            value=self._convert_value_to_db(setting_in.value, setting_in.value_type),
            value_type=setting_in.value_type,
            description=setting_in.description,
        )
        self.session.add(db_setting)
        await self.session.commit()
        await self.session.refresh(db_setting)
        return db_setting

    async def update_setting(
        self, setting: SystemSettings, setting_in: SystemSettingUpdate
    ) -> SystemSettings:
        """Update an existing system setting."""
        if setting_in.description is not None:
            setting.description = setting_in.description
        if setting_in.value is not None and setting_in.value_type is not None:
            setting.value = self._convert_value_to_db(setting_in.value, setting_in.value_type)
            setting.value_type = setting_in.value_type
        
        await self.session.commit()
        await self.session.refresh(setting)
        return setting

    async def delete_setting(self, setting: SystemSettings):
        """Delete a system setting."""
        await self.session.delete(setting)
        await self.session.commit()

    def _convert_value_to_db(self, value: Any, value_type: str) -> str:
        """Converts a Python value to its string representation for database storage."""
        if value_type == "boolean":
            return "true" if value else "false"
        return str(value)

    def _convert_value_from_db(self, value: str, value_type: str) -> Any:
        """Converts a string value from the database to its Python type."""
        if value_type == "boolean":
            return value.lower() == "true"
        elif value_type == "integer":
            return int(value)
        elif value_type == "float":
            return float(value)
        elif value_type == "uuid":
            return UUID(value)
        # Default to string if type is unknown or not specified
        return value

    async def set_maintenance_mode(self, enable: bool, message: Optional[str] = None):
        """
        Enables or disables maintenance mode.
        If enabling, an optional message can be provided.
        """
        maintenance_setting = await self.get_setting("maintenance_mode")
        maintenance_message_setting = await self.get_setting("maintenance_mode_message")

        if enable:
            if not maintenance_setting:
                await self.create_setting(
                    SystemSettingCreate(
                        key="maintenance_mode", value=True, value_type="boolean", description="Enable or disable maintenance mode"
                    )
                )
            else:
                await self.update_setting(maintenance_setting, SystemSettingUpdate(value=True, value_type="boolean"))

            if message:
                if not maintenance_message_setting:
                    await self.create_setting(
                        SystemSettingCreate(
                            key="maintenance_mode_message", value=message, value_type="string", description="Message displayed during maintenance mode"
                        )
                    )
                else:
                    await self.update_setting(maintenance_message_setting, SystemSettingUpdate(value=message, value_type="string"))
            elif maintenance_message_setting:
                # If enabling and no message is provided, but a previous message exists, clear it.
                await self.update_setting(maintenance_message_setting, SystemSettingUpdate(value="", value_type="string"))
        else:
            if maintenance_setting:
                await self.update_setting(maintenance_setting, SystemSettingUpdate(value=False, value_type="boolean"))
            if maintenance_message_setting:
                await self.update_setting(maintenance_message_setting, SystemSettingUpdate(value="", value_type="string"))

    async def is_maintenance_mode_enabled(self) -> bool:
        """Checks if maintenance mode is currently enabled."""
        return await self.get_setting_value("maintenance_mode", default=False)

    async def get_maintenance_mode_message(self) -> str:
        """Gets the current maintenance mode message."""
        return await self.get_setting_value("maintenance_mode_message", default="The system is currently undergoing maintenance. Please check back soon.")
