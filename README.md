Introduction
============
PHP dev server using Python wsgiref. Some code taken from [Google App Engine SDK][1].

Usage
=====

    mkdir phpapp
    cd phpapp
    cat - > index.php
    <?php
    phpinfo();
    ^D
    python phpdev.py

Above will start a development server accesible at http://127.0.0.1:9000.

WARNING
=======
This is strictly for development only !

[1]:https://googleappengine.googlecode.com/svn/trunk/python/google/appengine/tools/devappserver2/php/runtime.py
