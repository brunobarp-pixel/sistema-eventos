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
        Schema::create('eventos', function (Blueprint $table) {
            $table->id();
            $table->string('nome');
            $table->text('descricao')->nullable();
            $table->text('conteudo')->nullable();
            $table->dateTime('data_inicio');
            $table->dateTime('data_fim');
            $table->string('local')->nullable();
            $table->string('cidade')->nullable();
            $table->string('estado')->nullable();
            $table->integer('vagas')->nullable();
            $table->integer('vagas_ocupadas')->default(0);
            $table->string('imagem')->nullable();
            $table->enum('status', ['planejamento', 'aberto', 'em_andamento', 'finalizado', 'cancelado'])->default('planejamento');
            $table->boolean('ativo')->default(true);
            $table->unsignedBigInteger('organizador_id')->nullable();
            $table->timestamps();
            $table->softDeletes();
            
            $table->foreign('organizador_id')->references('id')->on('usuarios')->onDelete('set null');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('eventos');
    }
};
