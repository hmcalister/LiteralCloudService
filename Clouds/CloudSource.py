import datetime
import urllib
import logging
import wget
import json
import os
import ssl
from ast import literal_eval
from typing import List, Tuple
from PIL import Image, UnidentifiedImageError

# To get around dodgy webcams with expired SSL certificates
ssl._create_default_https_context = ssl._create_unverified_context
logging.basicConfig(level=logging.INFO)

class CloudSource:
    """
    An object that holds information on a cloud source (a live webcam).
    This includes the URL to the webcam (to wget from) and the coords to crop at
    """

    def __init__(self, name: str, url: str, crop_coords: Tuple[int, int, int, int], time: str) -> None:
        """
        Create a new CloudSource given the required information.
        ---
        Params:
        name : str
            The name of this cloud source, used to identify the source and name files

        url : str
            The url to call with wget to get an image

        coords : Tuple[int, int, int, int]
            The coordinates to crop the image from in form of (left, top, right, bottom)
            To be used with PIL crop function

        time : str
            A time (in 24 hour format) to get the image from the url (since we want to avoid night)
            Currently relative to UTC, may add offsets later
            e.g. '10:24' or '23:11'
        """

        self.name = name
        self.url = url
        self.crop_coords = crop_coords
        self.time = time
        logging.debug(self.debug_str())

    def __str__(self) -> str:
        return (self.time.replace(":", "")) + "-" + self.name

    def __repr__(self) -> str:
        return str(self)

    def debug_str(self) -> str:
        """
        Return a debug of this cloud object as a string
        ---
        Returns : str
            A debug string of this objects attributes
        """

        return f"CloudSource: {self.name}, URL: {self.url}, crop_coords: {self.crop_coords}, Time: {self.time}"

    def get_image(self, image_name:str = None, directory:str="images/") -> bool:
        """
        Get the most recent image from this cloud source, crop it, and save it
        ---
        Params:
        image_name : str or None (optional, defaults to None)
            The name to save this image under. If left None, the default name is used
            The default name is date + self.name 
        ---
        Returns : bool
            True if image is successfully downloaded and cropped, false otherwise
        """

        logging.info(f"STARTING {self.name} DOWNLOAD")
        if image_name == None:
            image_name = f"{directory}{str(self)}.png"

        logging.debug(f"{image_name=}")
        logging.debug(f"{self.url=}")

        delete_file(image_name)

        try:
            wget.download(self.url, image_name)
        except ValueError as e:
            logging.info(f"ERROR: ValueError found during download of {self.name}! URL form not recognized")
            delete_file(image_name)
            logging.debug(f"{e=}")
            logging.debug(f"{type(e)=}")
            return False
        except urllib.error.HTTPError as e:
            logging.info(f"ERROR: HTTP error found during download of {self.name}! Check URL and retry")
            delete_file(image_name)
            logging.debug(f"{e=}")
            logging.debug(f"{type(e)=}")
            return False
        try:
            im = Image.open(image_name)
            im.close()
        except UnidentifiedImageError as e: 
            logging.info(f"ERROR: Unidentified image from source {self.name}! URL may be broken")
            delete_file(image_name)
            logging.debug(f"{e=}")
            logging.debug(f"{type(e)=}")
            return False

        logging.info("DOWNLOAD COMPLETE")
        logging.info("CROPPING IMAGE")
        logging.debug(f"Opening {image_name} with PIL")
        im = Image.open(image_name)
        logging.debug(f"Source Dimensions: {im.size}")
        logging.debug(f"Target Dimensions: {self.crop_coords=}")
        cropped_im = im.crop(self.crop_coords)
        logging.debug("Image cropped, saving image...")
        try:
            cropped_im.save(image_name)
        except SystemError as e:
            logging.info(f"ERROR: System error during save of {self.name}! Check config and retry")
            delete_file(image_name)
            logging.debug(f"{e=}")
            logging.debug(f"{type(e)=}")
            return False
        logging.info("IMAGE SAVED")

        return True

    def set_target_time(self, now:datetime.datetime) -> datetime.datetime:
        """
        Given a time representing now (conventionally in UTC but depending on your sources configuration),
        return a datetime object that represents the time of this sources trigger.
        Also sets this object as a datafield of this CloudSource object

        ---

        Params
        now : datetime.datetime
            A datetime object representing now (conventionally in UTC but should be in a representation that fits your sources)
        
        ---
        
        Returns : datetime.datetime
            A datetime object representing the time at which this source should be triggered      
        """

        # Get hour and minute of this source
        hour = int(self.time.split(":")[0])
        minute = int(self.time.split(":")[1])
        self.target_time:datetime.datetime = now.replace(hour=hour, minute=minute, second=0)
        # If our target time is in the past, we must make the target time in the future by adding a day
        if self.target_time<now:
            self.target_time += datetime.timedelta(days=1)
        return self.target_time

def get_cloud_sources() -> List[CloudSource]:
    logging.info("LOAD DATA")
    data_file = open("Clouds/CloudSourcesData.json")
    # cloud_data = data_file.readlines()
    cloud_data = json.load(data_file)
    data_file.close()
    logging.info(cloud_data)
    logging.info("DATA LOADED")
    logging.info("-"*80)

    cloud_sources = []
    logging.info("LOAD SOURCES")
    for cloud_source_data in cloud_data["CloudSources"]:
        name = cloud_source_data["name"]
        url = cloud_source_data["url"]
        crop_coords = cloud_source_data["crop_coords"]
        for time in cloud_source_data["time_list"]:
            logging.info(f"{name}, {url}, {crop_coords}, {time}")
            cloud_source = CloudSource(name, url, literal_eval(crop_coords), time)
            logging.debug(cloud_source)
            cloud_sources.append(cloud_source)

    logging.info("SOURCES LOADED")

    return cloud_sources

def delete_file(file_path:str)->bool:
    """
    Delete a file located at file_path, handelling errors.
    ---
    Params
    file_path : str
        The path to the file to remove
    ---
    Returns : Bool
        True if the file no longer exists after method call
        False otherwise
    """

    if os.path.exists(file_path):
        logging.debug(f"REMOVING FILE {file_path}")
        try:
            os.remove(file_path)
        except IsADirectoryError as e:
            logging.info(f"ERROR: {file_path} is a directory")
            logging.debug(f"{e=}")
            logging.debug(f"{type(e)=}")
            return False
        except OSError as e:
            logging.info(f"ERROR: {file_path} CANNOT BE REMOVED")
            logging.debug(f"{e=}")
            logging.debug(f"{type(e)=}")
            return False
        logging.info(f"FILE REMOVED")
        return True
    else:
        logging.debug(f"{file_path} DOES NOT EXIST! REMOVAL NOT NEEDED")
        return True

if __name__ == "__main__":
    logging.getLogger().setLevel(level=logging.DEBUG)