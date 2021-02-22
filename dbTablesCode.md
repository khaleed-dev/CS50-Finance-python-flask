        #? CREATING DATABASE TABLES
        '''
            database transactions: 
            transactionID "primaryKey", users_id "foriegnKey", TypeOfTransaction "TEXT",
            stockSymbol CHAR(5), stockName, pricePerShare, timeOfTransaction "TEXT"
        '''
        # db.execute("""
        #         CREATE TABLE IF NOT EXISTS "transactions" (
        #         "id"	INTEGER UNIQUE NOT NULL,
        #         "users_id"	INTEGER NOT NULL,
        #         "TypeOfTransaction" "TEXT" NOT NULL,
        #         "stockSymbol"	TEXT NOT NULL,
        #         "stockName"	TEXT,
        #         "Price"	INTEGER NOT NULL,
        #         "Amount"	INTEGER NOT NULL,
        #         "time"	TEXT NOT NULL UNIQUE,
        #         FOREIGN KEY("users_id") REFERENCES "users"("id"),
        #         PRIMARY KEY("id" AUTOINCREMENT)
        #         )        
        # """)
        '''
            database stocks:
            user_id "foriegnKey", stockSymbol CHAR(5), stockName TEXT, Amount of shares (INT), price INT, total INT
        '''
        # db.execute("""
        #         CREATE TABLE IF NOT EXISTS "stocks" (
        #             "users_id"    INTEGER NOT NULL,
        #             "stockSymbol"	CHAR(5) NOT NULL,
        #             "amount"    INTEGER NOT NULL,
        #             FOREIGN KEY("users_id") REFERENCES "users"("id")
        #         )
        # """)