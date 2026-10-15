const mysql = require('mysql');
var crypto = require('crypto');
var express = require('express');
var bodyParser = require('body-parser');

const jwt = require('jsonwebtoken');
//const PORT = 3000;
const secretKey = process.env.JWT_SECRET;

const http = require('http');
//const express = require('express');
const port = 3000;

//connect database
const db = mysql.createConnection({
    host: process.env.DB_HOST,
    user: process.env.DB_USER,
    password: process.env.DB_PASSWORD,
    database: process.env.DB_NAME
});

if (!secretKey) {
    throw new Error('Missing JWT_SECRET environment variable.');
}
if (!process.env.DB_HOST || !process.env.DB_USER ||
    !process.env.DB_PASSWORD || !process.env.DB_NAME) {
    throw new Error('Missing database configuration environment variables.');
}

db.connect((err) => {
    if (err) {
        throw err;
    }
    console.log('MySQL Connected...');
});

//Password Ultil
var genRandomString = function(length){
	return crypto.randomBytes(Math.ceil(length/2))
	.toString('hex') /* convert to hex format*/
	.slice(0,length); /*return required number of Character*/
};


var sha512 = function(password,salt){
	var hash = crypto.createHmac('sha512',salt); //Use sha 512
	hash.update(password);
	var value = hash.digest('hex');
	return{
		salt:salt,
		passwordHash:value
	};
};


function saltHashPassword(userPassword){
	var salt = genRandomString(16); //generate random string with 16 characters to salt
	var passwordData = sha512(userPassword,salt);
	return passwordData;
}

function checkHasPassword(userPassword,salt)
{
	var passwordData = sha512(userPassword,salt);
	return passwordData;
}

//Create Express Service
var app = express();
app.use(bodyParser.json());    //Accept JSON Parameters
app.use(bodyParser.urlencoded({extended: true}));    //Accept URL Encoded Parameters


app.get('/', (req, res) => {
  res.status(200).send('Node.js is working with Express and http.');
});


// Create an HTTP server using the Express app
const server = http.createServer(app);

//-----------------------------------------------------------------
//Purpose : User Registration
//Parameters Field Name : userid, nanme, password
//Parameters : userid, nanme, password
//Retuen :  -
//-----------------------------------------------------------------
app.post('/register',(req,res,next)=>{
	var post_data = req.body; //Get POST parameters
	
	var plaint_password = post_data.password;  //Get password from post parameters
	var hash_data = saltHashPassword(plaint_password);
	var password = hash_data.passwordHash; //Get hash value
	var salt = hash_data.salt  //Get salt
	
	var name = post_data.name;
	var userid = post_data.userid;
	
	db.query('SELECT * FROM userProfiles where userid=?',[userid],function(err,result,fields){
		db.on('error', function(err){
			console.log('[Database Error]', err);
		});
	
		if(result && result.length)
			res.json('User already exist!');
		else
		{
			const sql = 'INSERT INTO userProfiles (userid, greeting, pin, salt, tid) values (?, ?, ?, ?, ?)';
			db.query(sql,[userid,name,password,salt,userid],function(err,result,fields){
		
				db.on('error', function(err){
					console.log('[Database Error]', err);
					res.json('User resgister error: ',err);
				});
		
				res.json('User register successfully!');
			})
		}
	});
})	


//-----------------------------------------------------------------
//Purpose : User Login
//Parameters Field Name : userid, password
//Parameters : userid, password
//Retuen :  token
//-----------------------------------------------------------------
app.post('/login',(req,res,next)=>{
	
	var post_data = req.body;
	
	//Extract userid and password from request
	var user_password = post_data.password;
	var userid = post_data.userid;
	
	
	const sql = 'SELECT * FROM userProfiles where userid=?';	
	
	db.query(sql,[userid],function(err,result,fields){
		db.on('error', function(err){
			console.log('[Database Error]', err);
		});
	
		if(result && result.length)
		{
			var salt = result[0].salt; //get salt of result if account exist
			var encrypted_password = result[0].pin;
			
			// Hash password from Login request with salt in Database
			var hashed_password = checkHasPassword(user_password,salt).passwordHash;

/* For Debug the password			
			console.log(user_password);
			console.log(salt);
			console.log(encrypted_password);
			console.log(hashed_password);
*/
			
			if(encrypted_password==hashed_password)
			{	
				//res.end(JSON.stringify(result[0]))   //if password is true, return all infomarion of user			
				var token = jwt.sign({ id: userid }, secretKey, { expiresIn: '1h' });
				res.status(200).json({ token });			
			}
			else
				//res.end(JSON.stringify('Invalid password'));
				return res.status(401).send('Invalid password.');
			
		}	
		else
		{
			res.json('User not exist!');
		}
	});
	
})


//-----------------------------------------------------------------
//Purpose : Change User Password
//Parameters Field Name : userid, old_password, password
//Parameters : userid, old_password, new password
//Retuen :  -
//-----------------------------------------------------------------
app.post('/change_password',(req,res,next)=>{
	var post_data = req.body; //Get POST parameters

//Extract email, new password, confirm new password and old password from request
	var plaint_password = post_data.new_password;              //Get new password from post parameters
	var old_password = post_data.old_password;                 //Get old password from post parameters	
	var userid = post_data.userid;                               //Get email from post parameters
		
	db.query('SELECT * FROM userProfiles where userid=?',[userid],function(err,result,fields){
		db.on('error', function(err){
			console.log('[Database Error]', err);
		});

		if(result && result.length)
		{
			var check_salt = result[0].salt; //get salt of result if account exist
			var encrypted_password = result[0].pin;
			
			// Hash password from Login request with salt in Database
			var hashed_password = checkHasPassword(old_password,check_salt).passwordHash;

/* For Debug the password			
			console.log(user_password);
			console.log(salt);
			console.log(encrypted_password);
			console.log(hashed_password);
*/
		
			if(encrypted_password==hashed_password)
			{	
//if password is true, change usr password
				var hash_data = saltHashPassword(plaint_password);
				var password = hash_data.passwordHash;              //Get hash value
				var salt = hash_data.salt                           //Get salt

				db.query('UPDATE userProfiles SET pin=?, salt=? WHERE userid=?',[password,salt,userid],function(err,result,fields){
			
					db.on('error', function(err){
						console.log('[Database Error]', err);
						res.json('Fail to change user password : ',err);
					});
			
					res.json('Changed user password successfully');
				})
			}
			else
			{	
					res.json('Wrong password');
					//res.end(JSON.stringify('Wrong password'));
			}	
		}	
		else
		{
			res.json('User not exist!');
		}
	});
})	

//-----------------------------------------------------------------
//Purpose : Server setting for server user password and notification Flag
//Parameters Field Name : userid, password, notify
//Parameters Value : userid, server user password, notification Flag
//Retuen :  -
//-----------------------------------------------------------------
app.post('/server_setting',(req,res,next)=>{
	
	var post_data = req.body;
	
	//Extract userid, notify and password from request
	var user_password = post_data.password;
	var userid = post_data.userid;
	var notifyme = post_data.notify;
	
	db.query('SELECT * FROM userProfiles where userid=?',[userid],function(err,result,fields){
		db.on('error', function(err){
			console.log('[Database Error]', err);
		});
	
		if(result && result.length)
		{
			db.query('UPDATE userProfiles SET tpin=?, notify=? WHERE userid=?',[user_password,notifyme,userid],function(err,result,fields){
		
				db.on('error', function(err){
					console.log('[Database Error]', err);
					res.json('Server setting update error: ',err);
				});
		
				res.json('Server setting updated successfully');
			})
		}	
		else
		{
			res.json('User not exist!');
		}
	});
	
});

//-----------------------------------------------------------------
//Purpose : Update Mobile Token Settings, Parameters : userid, token for FCM
//Parameters Field Name : userid, token
//Parameters Value : userid, sMobile Token
//Retuen :  -
//-----------------------------------------------------------------
app.post('/token',(req,res,next)=>{
	
	var post_data = req.body;
	
	//Extract userid and token from request
	var user_token = post_data.token;
	var userid = post_data.userid;
	
	db.query('SELECT * FROM userProfiles where userid=?',[userid],function(err,result,fields){
		db.on('error', function(err){
			console.log('[Database Error]', err);
		});
	
		if(result && result.length)
		{
			db.query('UPDATE userProfiles SET token=? WHERE userid=?',[user_token,userid],function(err,result,fields){
		
				db.on('error', function(err){
					console.log('[Database Error]', err);
					res.json('Token update error: ',err);
				});
		
				res.json('Token updated successfully');
			})
		}	
		else
		{
			res.json('User not exist!');
		}
	});
	
})


//-----------------------------------------------------------------
//Purpose : Select Pricing Data
//Parameters Field Name : -
//Parameters Value : -
//Retuen :  selected data
//-----------------------------------------------------------------

app.get('/price_data', (req, res) => {
    db.query('SELECT * FROM _v_rates_for_today_threshold', (err, results) => {
        if (err) {
            res.status(500).send('Error retrieving prices');
            return;
        }
        res.json(results);
    });
});


//-----------------------------------------------------------------
//Purpose : Select Devices with schedules Data, Paremeters : userid, dummy (no use, for avoid email at the http URL end
//Parameters Field Name : userid, dummy
//Parameters Value : userid, 1
//Retuen :  selected data
//-----------------------------------------------------------------

app.get('/devices_schedule/:userid/:temp', (req, res) => {
	
	const user_id = req.params.userid;
	//var user_id = post_data.userid;
//	console.log(req.params.userid);
//	console.log(user_id);
	
//	console.log(`Extracted user_id parameter: ${user_id}`); // Log to check extracted value

	const sql = 'SELECT d.*, s.schedule_id, s.start_time,s.end_time,s.`status` AS schedule_staus, s.enabled AS schedule_enabled FROM userDevices d INNER JOIN schedules s ON d.userid = s.userid AND d.ip = s.ip WHERE d.userid=? ORDER BY d.ip ASC, s.start_time ASC'

/*
	const sql = 'SELECT d.*, s.schedule_id, s.start_time,s.end_time,s.`status` AS schedule_staus, s.enabled AS schedule_enabled FROM userDevices d INNER JOIN schedules s ON d.userid = s.userid AND d.ip = s.ip ORDER BY d.ip ASC, s.start_time ASC'
*/
    db.query(sql,[user_id], (err, results) => {
        if (err) {
            res.status(500).send('Error retrieving devices schedule!');
            return;
        }
        res.json(results);
    });
});



server.listen(port, () => {
  console.log(`Server running`);
});