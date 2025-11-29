<?php

return [
    /*
    |--------------------------------------------------------------------------
    | Cross-Origin Resource Sharing (CORS) Configuration
    |--------------------------------------------------------------------------
    |
    | Here you may configure CORS settings for your application. This
    | configuration is used by the CORS middleware to handle requests from
    | origins outside of your application.
    |
    */

    'paths' => ['api/*', 'sanctum/csrf-cookie'],

    'allowed_methods' => ['*'],

    'allowed_origins' => [
        'http://177.44.248.118',
        'http://177.44.248.118:8080',
        'http://127.0.0.1',
        'http://localhost',
        'http://localhost:8080',
        'http://localhost:3000',
    ],

    'allowed_origins_patterns' => ['*'],

    'allowed_headers' => ['*'],

    'exposed_headers' => [],

    'max_age' => 0,

    'supports_credentials' => true,
];
