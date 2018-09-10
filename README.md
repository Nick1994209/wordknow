# WORDKNOW

### Telegram bot @wordknow

    bot for learning new words

#### Prepare

 * create db

        docker-compose run server python manage.py migrate

 * you can create user
 
        # create user: admin with password: pass
        docker-compose run server python manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_superuser('admin', '', 'pass')"

     
  * you can add words to db
  
        docker-compose run server python application/add_words.py
     
  * and run telegram_tasks, server, and telegram;
        
        docker-compose up
 
#### Application run

    docker-compose up
 
###### Add environments.env with secrets
    
    TELEGRAM_BOT_KEY='****-***'
    TELEGRAM_BOT_NAME='@your_bot_name'

    DEBUG=True

    # you can add proxy
    #http_proxy=host:port
    #https_proxy=host:port