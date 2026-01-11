"""Backfill time block names in day templates.

This script adds the 'name' field to existing time blocks in day templates
by fetching the name from the corresponding TimeBlockDefinition.
"""

import asyncio
from uuid import UUID

from lykke.infrastructure.database import async_session_maker
from lykke.infrastructure.repositories import (
    DayTemplateRepository,
    TimeBlockDefinitionRepository,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def backfill_time_block_names() -> None:
    """Backfill time block names for all day templates."""
    async with async_session_maker() as session:
        session = AsyncSession(bind=session.bind)
        
        # Get all unique user_ids from day_templates
        from lykke.infrastructure.database.tables import day_templates_tbl
        
        stmt = select(day_templates_tbl.c.user_id).distinct()
        result = await session.execute(stmt)
        user_ids = [row[0] for row in result]
        
        print(f"Found {len(user_ids)} users with day templates")
        
        for user_id in user_ids:
            print(f"\nProcessing user {user_id}...")
            
            day_template_repo = DayTemplateRepository(user_id=user_id)
            time_block_def_repo = TimeBlockDefinitionRepository(user_id=user_id)
            
            # Get all day templates for this user
            templates = await day_template_repo.all()
            
            for template in templates:
                if not template.time_blocks:
                    continue
                
                print(f"  Checking template '{template.slug}'...")
                updated = False
                updated_time_blocks = []
                
                for tb in template.time_blocks:
                    # Check if name is missing or is the default placeholder
                    if not hasattr(tb, 'name') or tb.name == "Time Block":
                        try:
                            # Fetch the TimeBlockDefinition
                            time_block_def = await time_block_def_repo.get(
                                tb.time_block_definition_id
                            )
                            # Create updated time block with name
                            from lykke.domain import value_objects
                            
                            updated_tb = value_objects.DayTemplateTimeBlock(
                                time_block_definition_id=tb.time_block_definition_id,
                                start_time=tb.start_time,
                                end_time=tb.end_time,
                                name=time_block_def.name,
                            )
                            updated_time_blocks.append(updated_tb)
                            updated = True
                            print(f"    Updated time block with name: {time_block_def.name}")
                        except Exception as e:
                            print(f"    Warning: Could not fetch definition for {tb.time_block_definition_id}: {e}")
                            # Keep the original if we can't fetch the definition
                            updated_time_blocks.append(tb)
                    else:
                        updated_time_blocks.append(tb)
                
                if updated:
                    # Save the updated template
                    from lykke.domain.entities.day_template import DayTemplateEntity
                    
                    updated_template = DayTemplateEntity(
                        id=template.id,
                        user_id=template.user_id,
                        slug=template.slug,
                        alarm=template.alarm,
                        icon=template.icon,
                        routine_ids=template.routine_ids,
                        time_blocks=updated_time_blocks,
                    )
                    await day_template_repo.put(updated_template)
                    print(f"    Saved updated template")
        
        print("\n✅ Migration complete!")


if __name__ == "__main__":
    asyncio.run(backfill_time_block_names())
