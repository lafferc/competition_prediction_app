AC_INIT([prediction-app], [0.13.0], [lafferc@tcd.ie])

AC_SUBST([target_dir], [/var/www/html/gamlaffo/])
AC_SUBST([media_dir], [/var/www/media/])

os=`head -1 /etc/issue`
case $os in
    Ubuntu*)
        AC_MSG_NOTICE([Config for ubuntu])
        AC_SUBST([webserver], [apache2])
        AC_SUBST([webuser], [www-data])
        AC_SUBST([webdir], [/etc/apache2/sites-available/])
        ;;
    *)
        # default is centos
        AC_MSG_NOTICE([Config for centos])
        AC_SUBST([webserver], [httpd])
        AC_SUBST([webuser], [apache])
        AC_SUBST([webdir], [/etc/httpd/conf.d/])
        ;;
esac

AC_CONFIG_FILES([Makefile])
AC_OUTPUT
