import React from "react";
import type { Anuidade } from "@/types/membros";
import type { DisponibilidadePagamento } from "@/types/pagamentos";
import { cobrarAnuidade } from "@/services/pagamentos";
import PagamentoModal from "./PagamentoModal";

interface Props {
  anuidade: Anuidade;
  disponibilidade: DisponibilidadePagamento;
  onClose: () => void;
  onPago: () => void;
}

export default function PagarAnuidadeModal({ anuidade, disponibilidade, onClose, onPago }: Props) {
  const valor = `R$ ${parseFloat(anuidade.valor).toFixed(2).replace(".", ",")}`;
  return (
    <PagamentoModal
      titulo={`Anuidade ${anuidade.ano_referencia} — ${valor}`}
      mensagemPago={`Sua anuidade ${anuidade.ano_referencia} está quitada. Obrigado!`}
      gerar={(metodo) => cobrarAnuidade(anuidade.id, metodo)}
      disponibilidade={disponibilidade}
      onClose={onClose}
      onPago={onPago}
    />
  );
}
