<!doctype html>
<html lang="pt-BR" class="dark">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="csrf-token" content="{{ csrf_token() }}">
    <title>@yield('title', 'Brasil Minis | Sua paixão em miniatura')</title>
    <meta name="description" content="@yield('meta_description', 'Miniaturas colecionáveis, acessórios e vestuário automotivo premium. Sua paixão em miniatura.')">
    @vite(['resources/css/app.css', 'resources/js/app.js'])
</head>
<body class="min-h-screen flex flex-col bg-bm-black">
    @include('partials.header')

    <main class="flex-1">
        @include('partials.flash')
        @yield('content')
    </main>

    @include('partials.footer')
</body>
</html>
