import logging, datetime, time, json
import numpy as np

logging.Formatter.converter = time.gmtime
logging.basicConfig(filename=f"logs/{str(datetime.datetime.utcnow().date())}-cloud-sources.log", 
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

from Clouds import CloudSource

NUM_IMAGES = 12

ONE_DAY = 24*60*60
ONE_HOUR = 60*60
NUM_IMAGES = 48
BASE_IMAGE_TIMES = np.linspace(0, ONE_DAY, NUM_IMAGES)

logging.info("-"*80)
logging.info("*"*80)
logging.info(f"RECREATE SOURCE TIMES")
logging.info("*"*80)
logging.info("-"*80)

with open("Clouds/CloudSourcesData.json", "r") as f:
    cloudSourcesJSON = json.load(f)
    for source in cloudSourcesJSON["CloudSources"]:
        randomOffsets = np.random.uniform(size=(NUM_IMAGES, )) * ONE_HOUR
        sourceImageTimes = BASE_IMAGE_TIMES + randomOffsets
        imageTimesUTC = [datetime.datetime.utcfromtimestamp(t).strftime("%H:%M") for t in sourceImageTimes]
        source["time_list"] = imageTimesUTC

with open("Clouds/CloudSourcesData.json", "w") as f:
    json.dump(cloudSourcesJSON, f)

logging.info("-"*80)
logging.info("*"*80)
logging.info(f"SCRIPT START AT LOCAL {datetime.datetime.now()}")
logging.info(f"SCRIPT START AT UTC {datetime.datetime.utcnow()}")
logging.info("*"*80)
logging.info("-"*80)

logging.info("LOAD SOURCES")
cloud_sources = CloudSource.get_cloud_sources()
logging.info("LOAD SUCCESSFUL")
logging.debug(cloud_sources)
logging.info("-"*80)

logging.info("SORTING SOURCES")
cloud_sources.sort(key = lambda x:x.target_time)
logging.info("SOURCES SORTED")
for source in cloud_sources:
    logging.info(f"{str(source):<50}{source.target_time}")

logging.info("-"*80)
logging.info(f"TOTAL OF {len(cloud_sources)} SOURCES")
logging.info("-"*80)

logging.info("START GET FROM SOURCES")
try:
    for source in cloud_sources:
        logging.info(f"{source=}")
        logging.info(f"CURRENT TIME (LOCAL): {datetime.datetime.now()}")
        logging.info(f"CURRENT TIME (UTC): {datetime.datetime.utcnow()}")
        now = datetime.datetime.utcnow()
        delta = source.target_time - now
        if delta.total_seconds() > 0:
            logging.info(f"SLEEPING FOR {delta.total_seconds()}s")
            logging.info(f"SLEEP FINISH SCHEDULED FOR (LOCAL): {datetime.datetime.now()+delta}")
            logging.info(f"SLEEP FINISH SCHEDULED FOR (UTC): {datetime.datetime.utcnow()+delta}")
            time.sleep(delta.total_seconds())
        else:
            logging.info(f"NO SLEEP NEEDED")
        logging.info(f"GET {str(source)}")
        if source.get_image():
            logging.info("GET SUCCESSFUL")
            logging.info("MOVE IMAGE TO ARCHIVE FOLDER")
            if CloudSource.archive_images():
                logging.info("IMAGE MOVED SUCCESSFULLY")
        else:
            logging.info("GET FAILED")
        logging.info("-"*80)
    logging.info("ALL SOURCES GET FINISHED")
    logging.info("-"*80)
except KeyboardInterrupt:
    logging.info("*"*80)
    logging.info("KEYBOARD INTERRUPT")
    logging.info("*"*80)

logging.info("MOVE REMAINING IMAGES TO ARCHIVE FOLDER")
CloudSource.archive_images()
logging.info("-"*80)