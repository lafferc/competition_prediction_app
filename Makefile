target_dir = /var/www/html/gamlaffo/
media_dir = /var/www/media/

install:
	echo "Installing " `cat VERSION`
	service httpd stop
	pip3 install -r requirements.txt
	mkdir $(target_dir)
	mkdir $(media_dir)
	rsync -rv --exclude=".*" . $(target_dir)
	$(target_dir)/manage.py collectstatic
	$(target_dir)/manage.py migrate
	chown -R apache:apache $(target_dir)
	chown -R apache:apache $(media_dir)
	cp gamlaffo.conf /etc/httpd/conf.d/
	service httpd start

update:
	echo "Upgrading to " `cat VERSION`
	service httpd stop
	pip3 install -r requirements.txt
	rsync -rv --exclude=".*" . $(target_dir)
	$(target_dir)/manage.py collectstatic --noinput
	cd $(target_dir); ./manage.py migrate; chown apache:apache *
	service httpd start

dev:
	echo "Installing dev env"
	pip3 install -r requirements.txt
	./manage.py migrate
