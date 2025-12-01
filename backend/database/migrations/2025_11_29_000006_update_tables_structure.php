<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        // Verificar e ajustar tabela usuarios
        if (!Schema::hasColumn('usuarios', 'email_verified_at')) {
            Schema::table('usuarios', function (Blueprint $table) {
                $table->timestamp('email_verified_at')->nullable()->after('email');
            });
        }

        if (!Schema::hasColumn('usuarios', 'remember_token')) {
            Schema::table('usuarios', function (Blueprint $table) {
                $table->string('remember_token')->nullable()->after('senha');
            });
        }

        // Verificar e ajustar tabela eventos
        if (!Schema::hasColumn('eventos', 'carga_horaria')) {
            Schema::table('eventos', function (Blueprint $table) {
                $table->integer('carga_horaria')->nullable()->after('local');
            });
        }

        if (!Schema::hasColumn('eventos', 'vagas_ocupadas')) {
            Schema::table('eventos', function (Blueprint $table) {
                $table->integer('vagas_ocupadas')->default(0)->after('vagas');
            });
        }

        if (!Schema::hasColumn('eventos', 'total_inscritos')) {
            Schema::table('eventos', function (Blueprint $table) {
                $table->integer('total_inscritos')->default(0)->after('vagas_ocupadas');
            });
        }

        // Verificar e ajustar tabela inscricoes
        if (!Schema::hasColumn('inscricoes', 'data_confirmacao')) {
            Schema::table('inscricoes', function (Blueprint $table) {
                $table->timestamp('data_confirmacao')->nullable()->after('status');
            });
        }

        // Verificar e ajustar tabela presencas
        if (!Schema::hasColumn('presencas', 'data_checkin')) {
            Schema::table('presencas', function (Blueprint $table) {
                $table->timestamp('data_checkin')->nullable()->after('data_presenca');
            });
        }

        if (!Schema::hasColumn('presencas', 'observacoes')) {
            Schema::table('presencas', function (Blueprint $table) {
                $table->text('observacoes')->nullable()->after('data_checkin');
            });
        }
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        // Reverter as alterações se necessário
        if (Schema::hasColumn('usuarios', 'email_verified_at')) {
            Schema::table('usuarios', function (Blueprint $table) {
                $table->dropColumn('email_verified_at');
            });
        }

        if (Schema::hasColumn('usuarios', 'remember_token')) {
            Schema::table('usuarios', function (Blueprint $table) {
                $table->dropColumn('remember_token');
            });
        }

        if (Schema::hasColumn('eventos', 'carga_horaria')) {
            Schema::table('eventos', function (Blueprint $table) {
                $table->dropColumn(['carga_horaria', 'vagas_ocupadas', 'total_inscritos']);
            });
        }

        if (Schema::hasColumn('inscricoes', 'data_confirmacao')) {
            Schema::table('inscricoes', function (Blueprint $table) {
                $table->dropColumn('data_confirmacao');
            });
        }

        if (Schema::hasColumn('presencas', 'data_checkin')) {
            Schema::table('presencas', function (Blueprint $table) {
                $table->dropColumn(['data_checkin', 'observacoes']);
            });
        }
    }
};