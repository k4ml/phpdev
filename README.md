Introduction
============
PHP dev server using Python wsgiref. Some code taken from [Google App Engine SDK][1]. It require `php5-cgi`
binary available in `PATH`. Tested on Ubuntu 12.04.

Usage
=====

    mkdir phpapp
    cd phpapp
    cat - > index.php
    <?php
    phpinfo();
    ^D
    wget https://raw.github.com/k4ml/phpdev/master/phpdev.py
    python phpdev.py

Above will start a development server accesible at http://127.0.0.1:8080. You can specify other directory as
document root:-

    python phpdev.py -d www

WARNING
=======
This is strictly for development only !

Applications
============
The following applications has been tested and working fine:-

* WolfCMS - http://www.wolfcms.org/
* Drupal 7 - work fine but very slow.

[1]:https://googleappengine.googlecode.com/svn/trunk/python/google/appengine/tools/devappserver2/php/runtime.py
