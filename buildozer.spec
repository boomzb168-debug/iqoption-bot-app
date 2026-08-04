[app]
title = IQ Option Bot
package.name = iqbot
package.domain = org.iqbot

# (str) Source directory where the application lives
source.dir = .

# (list) Source files to include (let it be empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas

# (str) Application versioning
version = 0.1

# (list) Application requirements
requirements = python3,kivy,requests,urllib3,certifi,idna,charset-normalizer

# (str) Supported orientations
orientation = portrait

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 24

# (str) Android permissions
android.permissions = INTERNET
