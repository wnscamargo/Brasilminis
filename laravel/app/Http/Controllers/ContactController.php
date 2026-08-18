<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;

class ContactController extends Controller
{
    public function index()
    {
        return view('shop.contact');
    }

    public function send(Request $request)
    {
        $request->validate([
            'name' => 'required|string',
            'email' => 'required|email',
            'message' => 'required|string',
        ]);

        // MOCKED: apenas registra em log. Trocar por Mail/Notification em produção.
        logger()->info('Contato Brasil Minis', $request->only('name', 'email', 'message'));

        return back()->with('success', 'Mensagem enviada! Retornaremos em breve.');
    }
}
