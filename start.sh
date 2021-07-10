if [[ -n $TOKEN_PICKLE_URL ]]; then
	apt-get install wget
	wget -q $TOKEN_PICKLE_URL -O /usr/src/app/token.pickle
fi

if [[ -n $ACCOUNTS_ZIP_URL ]]; then
	apt-get install unzip
	wget -q $ACCOUNTS_ZIP_URL -O /usr/src/app/accounts.zip
	unzip accounts.zip -d /usr/src/app/accounts
	rm accounts.zip
fi

python3 -m bot
