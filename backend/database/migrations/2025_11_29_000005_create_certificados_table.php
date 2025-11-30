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
        Schema::create('certificados', function (Blueprint $table) {
            $table->id();
            $table->unsignedBigInteger('usuario_id');
            $table->unsignedBigInteger('evento_id');
            $table->unsignedBigInteger('inscricao_id')->nullable();
            $table->string('codigo_validacao')->unique();
            $table->timestamp('data_emissao');
            $table->string('arquivo_pdf')->nullable();
            $table->boolean('enviado_email')->default(false);
            $table->timestamps();
            $table->softDeletes();

            // Foreign keys
            $table->foreign('usuario_id')->references('id')->on('usuarios')->onDelete('cascade');
            $table->foreign('evento_id')->references('id')->on('eventos')->onDelete('cascade');
            $table->foreign('inscricao_id')->references('id')->on('inscricoes')->onDelete('set null');
            
            // Indexes
            $table->index(['usuario_id', 'evento_id']);
            $table->index('codigo_validacao');
            $table->index('data_emissao');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('certificados');
    }
};