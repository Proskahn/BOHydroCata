import asyncio
import os
import glob
import logging
from hydrocata.storage.database_storage import DatabaseStorage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def clean_all_databases():
    """Delete all experiments from experiments.db and remove all .db files."""
    confirm = input("WARNING: This will delete all .db files, including experiments.db. Proceed? (y/n): ")
    if confirm.lower() != 'y':
        logger.info("Cleanup aborted.")
        return

    try:
        storage = DatabaseStorage(db_path="sqlite:///experiments.db")
        experiments = await storage.list_experiments()
        for exp in experiments:
            experiment_name = exp["name"]
            await storage.delete_experiment(experiment_name)
            logger.info(f"Deleted experiment: {experiment_name}")
    except Exception as e:
        logger.error(f"Failed to clean experiments.db: {str(e)}")

    db_files = glob.glob("*.db") + glob.glob("**/test_experiments_*.db", recursive=True)
    for db_file in db_files:
        try:
            if os.path.exists(db_file):
                os.remove(db_file)
                logger.info(f"Deleted database file: {db_file}")
        except Exception as e:
            logger.error(f"Failed to delete {db_file}: {str(e)}")

if __name__ == "__main__":
    asyncio.run(clean_all_databases())
