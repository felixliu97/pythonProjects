from loguru import logger

bottles_count = 99
logger.debug(f"{bottles_count} bottles of beer on the wall, {bottles_count} bottles of beer. Take one down pass it around.")
bottles_count -= 1
logger.info(f"{bottles_count} bottles of beer on the wall, {bottles_count} bottles of beer. Take one down pass it around.")
bottles_count -= 1
logger.success(f"{bottles_count} bottles of beer on the wall, {bottles_count} bottles of beer. Take one down pass it around.")
bottles_count -= 1
logger.warning(f"{bottles_count} bottles of beer on the wall, {bottles_count} bottles of beer. Take one down pass it around.")
bottles_count -= 1
logger.error(f"{bottles_count} bottles of beer on the wall, {bottles_count} bottles of beer. Take one down pass it around.")
bottles_count -= 1
logger.critical(f"{bottles_count} bottles of beer on the wall, {bottles_count} bottles of beer. Take one down pass it around.")
