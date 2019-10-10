from os import path
from time import sleep

from cothread.catools import caput, caget

from .util import mkdir_p, time_stamp


def backup_zebra(
        name, backup_directory, property_list, my_email, num_retries=3
):
    # Amend the backup file path
    Path = path.join(backup_directory, "Zebras/")
    mkdir_p(Path)
    Path += str(name) + "_" + time_stamp()

    for AttemptNum in range(num_retries):
        # noinspection PyBroadException
        try:
            print("Backing up Zebra " + name + ". Attempt " + str(
                AttemptNum + 1) + " of " + str(num_retries))
            caput('%s:%s' % (str(name), 'CONFIG_FILE'), Path, datatype=999)
            caput('%s:%s' % (str(name), 'CONFIG_WRITE.PROC'), 1, timeout=30,
                  wait=True)
            # Store button PV triggered successfully
            pv = caget('%s:%s' % (str(name), 'CONFIG_STATUS'),
                       datatype=999)
            while pv == "Writing '" + Path + "'":
                # Waiting for write to complete
                sleep(1)
                pv = caget('%s:%s' % (str(name), 'CONFIG_STATUS'),
                           datatype=999)
            if pv == "Too soon, initial poll not completed, wait a " \
                     "minute":
                print(pv)
                print("Waiting 3 seconds...")
                sleep(3)
                raise
            elif pv == "Can't open '" + Path + "'":
                print(pv)
                raise
            elif pv == "Done":
                print("Finished backing up Zebra " + name)
                property_list.append("Successful")

        except TimeoutError:
            error_message = "ERROR: Timeout connecting to {} is the IOC up?"
            error_message.format(name)
            my_email.add_to_message(error_message)
        except BaseException:
            error_message = "ERROR: Problem backing up " + name
            my_email.add_to_message(error_message)
            continue
        break
    else:
        error_message = "\nAll " + str(
            num_retries) + " attempts to backup " + name + " failed"
        my_email.add_to_message(error_message)
        print(error_message)
        property_list.append("Failed")
