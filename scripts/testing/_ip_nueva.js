// El registro tiene límite por IP, por hora y por día: quien registra muchas veces contra una misma base
// manda en X-Forwarded-For una IP inventada distinta cada vez.
module.exports = () => '10.' + [0, 0, 0].map(() => Math.floor(Math.random() * 256)).join('.');
