if [[ -n $TOKEN_PICKLE_URL ]]; then
	wget -q $TOKEN_PICKLE_URL -O ./token.pickle
fi

if [[ -n $ACCOUNTS_ZIP_URL ]]; then
	wget -q $ACCOUNTS_ZIP_URL -O ./accounts.zip
	unzip accounts.zip -d ./accounts
	rm accounts.zip
fi

python3 -m bot
