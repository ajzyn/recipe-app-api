# Dockerfile to obraz, a docker-compose pozwala nam na odpalania i konifgurowanie wielu obrazów z których składa się aplikacja
# ALPINE to najlżejsze wersje pajtona
# żeby nie mieć limitów podczas pobierania tego obrazu podczas budowania aplikacji na github actions, musze zalogować się do docker hub w github actions
FROM python:3.9-alpine3.13
# kto utrzymuje kod
LABEL maintainer="ajzyn"

# czasami outputy pythona są buforowane i wyświetlane zbiorczo. poniższa komenda pozwala nam uniknąć tego i pokazuje natychmiastowo output ( np. logi )
ENV PYTHONUNBUFFERED 1

# kopiuje requiremenety do katalogu tymaczasowego
COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt
# kopiuje applikację do folderu app PODCZAS PROCESU BUDOWY OBRAZU !!!!!! pozwala to na odpalanie już zbudowanego obrazu bez potrzeby posiadania źródła kodu lokalnie
COPY ./app /app
# ustawia working directory, czyli ustawia katalog roboczy dla wszystkich kolejnych instrukcji w Dockerfile !
WORKDIR /app
# port który jest udostępnianiny na zewątrz aplikacji do naszego kompa/servera
EXPOSE 8000

# określa argument ( w sumie to coś jak zmienną srodowiskowa), który może być nadpisany podczas odpalania projektu ( np. w docker-compose możemy nadpisać ten argument)
ARG DEV=false

# każdy RUN( czy komenda ) tworzy nowy layer obrazu, więc im mniej ich tym lepiej
# tworzy virtual environemtn pythona w folderze /py
RUN python -m venv /py && \
    # upgejduje pip
    /py/bin/pip install --upgrade pip && \
    # instaluje paczkę która jest potrzeba do łącznie z postgres - adapter
    apk add --update --no-cache postgresql-client && \
    # Ta opcja tworzy wirtualny pakiet o nazwie .tmp-build-deps, który jest zestawem tymczasowych zależności wymaganych do budowy aplikacji.
    #  Po zakończeniu procesu budowy te tymczasowe zależności mogą zostać łatwo usunięte za pomocą jednej komendy, co pomaga utrzymać obraz Docker w małym rozmiarze.
    apk add --update --no-cache --virtual .tmp-build-deps \
        build-base postgresql-dev musl-dev && \
    # instaluje requiremenety które były kopiowane w linij 10
    /py/bin/pip install -r /tmp/requirements.txt && \
    # jeżeli zmienna DEV === true to wykonuje blok if. zwróć uwagę, że muszą być spację pomiędzy [] i przed [
    if [ $DEV = "true" ]; \
        then /py/bin/pip install -r /tmp/requirements.dev.txt ; \
    # końcy blok if 
    fi && \    
    # usuwa fodler /tmp >>> rm = remove ; r = recursive ( czyli usuwa również pliki i folderu z wnętrza usuwanego katalogu ); f = force; /tmp = usuwany folder
    rm -rf /tmp && \
    apk del .tmp-build-deps && \
    # dodaje usera do linuxa, żeby nie używać roota ( niezalecena jest używanie roota ze względu na ewentualne ataki )
    adduser \
        --disabled-password \
        --no-create-home \
        django-user


# ustawia zmienną środowiskową która później pozwala na wykonywanie komend w terminalu bez wskazywania folderu w którym znajduje się m.in manage.py (?)
ENV PATH="/py/bin:$PATH"

# docker będize używał tego usera, który został wskazany jako ostatni w Dockerfile ( czyli poniższy user ), ew. root user jezeli nie wskażemy żadnego usera
USER django-user